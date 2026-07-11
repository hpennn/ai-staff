"""
认证路由 - 手机号验证码登录
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from database import get_db
import secrets
import hashlib
import re
import random
import time
from datetime import datetime, timedelta

router = APIRouter()

# ---- Pydantic models ----

class PhoneCodeRequest(BaseModel):
    phone: str


class PhoneLoginRequest(BaseModel):
    phone: str
    code: str


class AuthResponse(BaseModel):
    token: str
    phone: str


class MeResponse(BaseModel):
    id: int
    phone: str
    created_at: str


# ---- Auth dependency ----

async def get_current_admin(request: Request):
    """Extract and validate token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = auth_header[7:]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.token, s.admin_id, a.phone, a.created_at
        FROM sessions s
        JOIN admin a ON s.admin_id = a.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    return dict(row)


# ---- SMS utility ----

def _generate_code() -> str:
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def _validate_phone(phone: str) -> bool:
    return bool(re.match(r'^1[3-9]\d{9}$', phone))


# ---- Routes ----

@router.get("/auth/status")
async def auth_status():
    """Check if admin exists (used by frontend to decide register vs login)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM admin")
    cnt = cursor.fetchone()["cnt"]
    conn.close()
    return {"has_admin": cnt > 0}


@router.post("/auth/send-code")
async def send_verification_code(req: PhoneCodeRequest):
    """发送手机验证码（首次自动注册）"""
    phone = req.phone.strip()

    if not _validate_phone(phone):
        raise HTTPException(status_code=400, detail="请输入正确的手机号码")

    # 检查发送频率限制
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT created_at FROM phone_codes 
        WHERE phone = ? ORDER BY created_at DESC LIMIT 1
    """, (phone,))
    last = cursor.fetchone()
    if last:
        last_time = datetime.fromisoformat(last["created_at"])
        if (datetime.now() - last_time).total_seconds() < 60:
            conn.close()
            raise HTTPException(status_code=429, detail="验证码发送过于频繁，请60秒后重试")

    # 生成验证码
    code = _generate_code()

    # 存储验证码（5分钟有效）
    cursor.execute("""
        INSERT INTO phone_codes (phone, code, expires_at)
        VALUES (?, ?, datetime('now', '+5 minutes'))
    """, (phone, code))
    conn.commit()
    conn.close()

    # TODO: 接入真实短信服务（阿里云/腾讯云 SMS）
    # 当前开发阶段：验证码通过API响应返回，生产环境请接入短信服务商
    return {
        "message": "验证码已发送",
        "code": code,  # 开发阶段返回验证码，生产环境删除此行
        "expire_seconds": 300
    }


@router.post("/auth/phone-login")
async def phone_login(req: PhoneLoginRequest):
    """手机号验证码登录（自动注册）"""
    phone = req.phone.strip()
    code = req.code.strip()

    if not _validate_phone(phone):
        raise HTTPException(status_code=400, detail="请输入正确的手机号码")
    if not code:
        raise HTTPException(status_code=400, detail="请输入验证码")

    conn = get_db()
    cursor = conn.cursor()

    # 验证验证码
    cursor.execute("""
        SELECT id FROM phone_codes 
        WHERE phone = ? AND code = ? AND expires_at > datetime('now')
        ORDER BY created_at DESC LIMIT 1
    """, (phone, code))
    code_row = cursor.fetchone()

    if not code_row:
        conn.close()
        raise HTTPException(status_code=401, detail="验证码错误或已过期")

    # 验证码使用后立即删除
    cursor.execute("DELETE FROM phone_codes WHERE phone = ?", (phone,))

    # 查找或创建管理员
    cursor.execute("SELECT id, phone FROM admin WHERE phone = ?", (phone,))
    admin = cursor.fetchone()

    if not admin:
        # 首次登录自动注册
        cursor.execute("INSERT INTO admin (phone) VALUES (?)", (phone,))
        conn.commit()
        admin_id = cursor.lastrowid
    else:
        admin_id = admin["id"]

    # 创建会话
    token = secrets.token_hex(32)
    cursor.execute(
        "INSERT INTO sessions (token, admin_id) VALUES (?, ?)",
        (token, admin_id)
    )
    conn.commit()
    conn.close()

    return {"token": token, "phone": phone}


@router.get("/auth/me")
async def me(admin: dict = Depends(get_current_admin)):
    """Get current admin info."""
    return {
        "id": admin["admin_id"],
        "phone": admin["phone"],
        "created_at": admin["created_at"]
    }


@router.post("/auth/logout")
async def logout(request: Request):
    """Logout: delete session."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    return {"message": "已退出登录"}
