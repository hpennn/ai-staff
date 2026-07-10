from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from database import get_db
import secrets
import hashlib

router = APIRouter()
security = HTTPBearer(auto_error=False)

SALT = "ai-staff-salt-2026"


def hash_password(password: str) -> str:
    return hashlib.sha256(f"{SALT}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


# ---- Pydantic models ----

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str


class MeResponse(BaseModel):
    id: int
    username: str
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
        SELECT s.token, s.admin_id, a.username, a.created_at
        FROM sessions s
        JOIN admin a ON s.admin_id = a.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    return dict(row)


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


@router.post("/auth/register")
async def register(req: RegisterRequest):
    """Register admin (only when no admin exists)."""
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    conn = get_db()
    cursor = conn.cursor()

    # Check if any admin exists
    cursor.execute("SELECT COUNT(*) as cnt FROM admin")
    cnt = cursor.fetchone()["cnt"]
    if cnt > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="管理员已存在，请直接登录")

    # Create admin
    pw_hash = hash_password(req.password)
    cursor.execute(
        "INSERT INTO admin (username, password_hash) VALUES (?, ?)",
        (req.username, pw_hash)
    )
    conn.commit()
    admin_id = cursor.lastrowid

    # Auto-login: create session
    token = secrets.token_hex(32)
    cursor.execute(
        "INSERT INTO sessions (token, admin_id) VALUES (?, ?)",
        (token, admin_id)
    )
    conn.commit()
    conn.close()

    return {"token": token, "username": req.username}


@router.post("/auth/login")
async def login(req: LoginRequest):
    """Login and return token."""
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username = ?", (req.username,))
    admin = cursor.fetchone()

    if not admin or not verify_password(req.password, admin["password_hash"]):
        conn.close()
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Create session
    token = secrets.token_hex(32)
    cursor.execute(
        "INSERT INTO sessions (token, admin_id) VALUES (?, ?)",
        (token, admin["id"])
    )
    conn.commit()
    conn.close()

    return {"token": token, "username": req.username}


@router.get("/auth/me")
async def me(admin: dict = Depends(get_current_admin)):
    """Get current admin info."""
    return {
        "id": admin["admin_id"],
        "username": admin["username"],
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
