from fastapi import APIRouter, HTTPException
from database import get_db
from models import StaffCreate, StaffResponse, ConversationResponse, ConversationDetailResponse, SettingsUpdate, SettingsResponse
import json
import random

router = APIRouter()

AVATAR_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
    "#f97316", "#eab308", "#22c55e", "#14b8a6",
    "#06b6d4", "#3b82f6", "#6366f1", "#a855f7"
]


@router.get("/staff")
async def get_staff_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM staff ORDER BY created_at DESC")
    staff_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return staff_list


@router.post("/staff")
async def create_staff(staff: StaffCreate):
    conn = get_db()
    cursor = conn.cursor()

    # Process knowledge base
    kb = staff.knowledge_base or ""
    if kb.strip():
        lines = [line.strip() for line in kb.strip().split("\n") if line.strip()]
        kb_json = json.dumps(lines, ensure_ascii=False)
    else:
        kb_json = "[]"

    avatar_color = staff.avatar_color or random.choice(AVATAR_COLORS)

    cursor.execute(
        "INSERT INTO staff (name, role_description, knowledge_base, avatar_color) VALUES (?, ?, ?, ?)",
        (staff.name, staff.role_description, kb_json, avatar_color)
    )
    conn.commit()
    staff_id = cursor.lastrowid

    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    new_staff = dict(cursor.fetchone())
    conn.close()

    return new_staff


@router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    if not staff:
        conn.close()
        raise HTTPException(status_code=404, detail="员工不存在")

    cursor.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    cursor.execute("DELETE FROM conversation WHERE staff_id = ?", (staff_id,))
    conn.commit()
    conn.close()
    return {"message": "员工已删除"}


@router.get("/conversations")
async def get_conversations():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, s.name as staff_name, s.avatar_color
        FROM conversation c
        LEFT JOIN staff s ON c.staff_id = s.id
        ORDER BY c.created_at DESC
    """)
    conversations = []
    for row in cursor.fetchall():
        conv = dict(row)
        messages = json.loads(conv.get("messages", "[]"))
        last_msg = ""
        if messages:
            last_msg = messages[-1].get("content", "")[:50]
        conv["last_message"] = last_msg
        conversations.append(conv)
    conn.close()
    return conversations


@router.get("/conversations/{conv_id}")
async def get_conversation_detail(conv_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversation WHERE id = ?", (conv_id,))
    conv = cursor.fetchone()
    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="对话不存在")

    conv_dict = dict(conv)
    conv_dict["messages"] = json.loads(conv_dict.get("messages", "[]"))
    conn.close()
    return conv_dict


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversation WHERE id = ?", (conv_id,))
    conv = cursor.fetchone()
    if not conv:
        conn.close()
        raise HTTPException(status_code=404, detail="对话不存在")

    cursor.execute("DELETE FROM conversation WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()
    return {"message": "对话已删除"}


@router.get("/settings")
async def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row["key"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    return {
        "api_key": settings.get("api_key", ""),
        "model_id": settings.get("model_id", ""),
        "api_base_url": settings.get("api_base_url", "")
    }


@router.put("/settings")
async def update_settings(settings: SettingsUpdate):
    conn = get_db()
    cursor = conn.cursor()

    if settings.api_key is not None:
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('api_key', ?)",
            (settings.api_key,)
        )
    if settings.model_id is not None:
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('model_id', ?)",
            (settings.model_id,)
        )
    if settings.api_base_url is not None:
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('api_base_url', ?)",
            (settings.api_base_url,)
        )

    conn.commit()
    conn.close()
    return {"message": "设置已更新"}
