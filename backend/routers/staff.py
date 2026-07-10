from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from models import StaffCreate, StaffUpdate, StaffResponse, ConversationResponse, ConversationDetailResponse, SettingsUpdate, SettingsResponse
from routers.auth import get_current_admin
import json
import random

router = APIRouter()

AVATAR_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
    "#f97316", "#eab308", "#22c55e", "#14b8a6",
    "#06b6d4", "#3b82f6", "#6366f1", "#a855f7"
]


@router.get("/staff")
async def get_staff_list(admin: dict = Depends(get_current_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM staff ORDER BY created_at DESC")
    staff_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return staff_list


@router.post("/staff")
async def create_staff(staff: StaffCreate, admin: dict = Depends(get_current_admin)):
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
    platform = staff.platform or "通用"

    cursor.execute(
        "INSERT INTO staff (name, role_description, knowledge_base, avatar_color, platform) VALUES (?, ?, ?, ?, ?)",
        (staff.name, staff.role_description, kb_json, avatar_color, platform)
    )
    conn.commit()
    staff_id = cursor.lastrowid

    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    new_staff = dict(cursor.fetchone())
    conn.close()

    return new_staff


@router.put("/staff/{staff_id}")
async def update_staff(staff_id: int, staff: StaffUpdate, admin: dict = Depends(get_current_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="员工不存在")

    existing_dict = dict(existing)

    # Build update fields
    updates = {}
    if staff.name is not None:
        updates["name"] = staff.name
    if staff.role_description is not None:
        updates["role_description"] = staff.role_description
    if staff.knowledge_base is not None:
        kb = staff.knowledge_base
        if kb.strip():
            lines = [line.strip() for line in kb.strip().split("\n") if line.strip()]
            updates["knowledge_base"] = json.dumps(lines, ensure_ascii=False)
        else:
            updates["knowledge_base"] = "[]"
    if staff.avatar_color is not None:
        updates["avatar_color"] = staff.avatar_color
    if staff.platform is not None:
        updates["platform"] = staff.platform
    if staff.welcome_message is not None:
        updates["welcome_message"] = staff.welcome_message
    if staff.transfer_keywords is not None:
        updates["transfer_keywords"] = staff.transfer_keywords
    if staff.sensitive_words is not None:
        updates["sensitive_words"] = staff.sensitive_words
    if staff.auto_reply_rules is not None:
        updates["auto_reply_rules"] = staff.auto_reply_rules
    if staff.transfer_message is not None:
        updates["transfer_message"] = staff.transfer_message

    if updates:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [staff_id]
        cursor.execute(f"UPDATE staff SET {set_clause} WHERE id = ?", values)
        conn.commit()

    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    updated_staff = dict(cursor.fetchone())
    conn.close()

    return updated_staff


@router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: int, admin: dict = Depends(get_current_admin)):
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


@router.get("/staff/{staff_id}/stats")
async def get_staff_stats(staff_id: int, admin: dict = Depends(get_current_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    if not staff:
        conn.close()
        raise HTTPException(status_code=404, detail="员工不存在")

    # Total conversations
    cursor.execute("SELECT COUNT(*) as cnt FROM conversation WHERE staff_id = ?", (staff_id,))
    total_conversations = cursor.fetchone()["cnt"]

    # Today conversations
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM conversation 
        WHERE staff_id = ? AND DATE(created_at) = DATE('now', 'localtime')
    """, (staff_id,))
    today_conversations = cursor.fetchone()["cnt"]

    # Total messages
    cursor.execute("SELECT messages FROM conversation WHERE staff_id = ?", (staff_id,))
    total_messages = 0
    for row in cursor.fetchall():
        msgs = json.loads(row["messages"] or "[]")
        total_messages += len(msgs)

    # Today messages
    cursor.execute("""
        SELECT messages FROM conversation 
        WHERE staff_id = ? AND DATE(created_at) = DATE('now', 'localtime')
    """, (staff_id,))
    today_messages = 0
    for row in cursor.fetchall():
        msgs = json.loads(row["messages"] or "[]")
        today_messages += len(msgs)

    conn.close()

    return {
        "staff_id": staff_id,
        "total_conversations": total_conversations,
        "today_conversations": today_conversations,
        "total_messages": total_messages,
        "today_messages": today_messages
    }


@router.get("/stats/overview")
async def get_stats_overview(admin: dict = Depends(get_current_admin)):
    conn = get_db()
    cursor = conn.cursor()

    # Total conversations
    cursor.execute("SELECT COUNT(*) as cnt FROM conversation")
    total_conversations = cursor.fetchone()["cnt"]

    # Today conversations
    cursor.execute("SELECT COUNT(*) as cnt FROM conversation WHERE DATE(created_at) = DATE('now', 'localtime')")
    today_conversations = cursor.fetchone()["cnt"]

    # Total messages
    cursor.execute("SELECT messages FROM conversation")
    total_messages = 0
    for row in cursor.fetchall():
        msgs = json.loads(row["messages"] or "[]")
        total_messages += len(msgs)

    # Today messages
    cursor.execute("SELECT messages FROM conversation WHERE DATE(created_at) = DATE('now', 'localtime')")
    today_messages = 0
    for row in cursor.fetchall():
        msgs = json.loads(row["messages"] or "[]")
        today_messages += len(msgs)

    # Staff count
    cursor.execute("SELECT COUNT(*) as cnt FROM staff")
    staff_count = cursor.fetchone()["cnt"]

    # Per-staff ranking (by total messages)
    cursor.execute("SELECT id, name, avatar_color FROM staff")
    staff_ranking = []
    for s in cursor.fetchall():
        s_dict = dict(s)
        cursor2 = conn.cursor()
        cursor2.execute("SELECT COUNT(*) as cnt FROM conversation WHERE staff_id = ?", (s_dict["id"],))
        conv_count = cursor2.fetchone()["cnt"]

        cursor2.execute("SELECT messages FROM conversation WHERE staff_id = ?", (s_dict["id"],))
        msg_count = 0
        for row in cursor2.fetchall():
            msgs = json.loads(row["messages"] or "[]")
            msg_count += len(msgs)

        staff_ranking.append({
            "id": s_dict["id"],
            "name": s_dict["name"],
            "avatar_color": s_dict["avatar_color"],
            "conversations": conv_count,
            "messages": msg_count
        })

    # Sort by messages descending
    staff_ranking.sort(key=lambda x: x["messages"], reverse=True)

    conn.close()

    return {
        "total_conversations": total_conversations,
        "today_conversations": today_conversations,
        "total_messages": total_messages,
        "today_messages": today_messages,
        "staff_count": staff_count,
        "staff_ranking": staff_ranking
    }


@router.get("/conversations")
async def get_conversations(admin: dict = Depends(get_current_admin)):
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


@router.get("/staff/{staff_id}/conversations")
async def get_staff_conversations(staff_id: int, admin: dict = Depends(get_current_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    if not staff:
        conn.close()
        raise HTTPException(status_code=404, detail="员工不存在")

    cursor.execute("""
        SELECT c.*, s.name as staff_name, s.avatar_color
        FROM conversation c
        LEFT JOIN staff s ON c.staff_id = s.id
        WHERE c.staff_id = ?
        ORDER BY c.created_at DESC
    """, (staff_id,))
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
async def get_conversation_detail(conv_id: int, admin: dict = Depends(get_current_admin)):
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
async def delete_conversation(conv_id: int, admin: dict = Depends(get_current_admin)):
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
async def get_settings(admin: dict = Depends(get_current_admin)):
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
async def update_settings(settings: SettingsUpdate, admin: dict = Depends(get_current_admin)):
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
