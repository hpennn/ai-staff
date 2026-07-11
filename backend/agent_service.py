import httpx
import json
import os
from database import get_db

ARK_API_KEY = os.environ.get("ARK_API_KEY", "ark-4f063f47-ee3d-45a2-a6db-677cc71cf784-041e9")
MODEL_ID = os.environ.get("MODEL_ID", "ep-20260707225043-z7nkm")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")


def get_settings(admin_id: int = 0):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings WHERE admin_id = ?", (admin_id,))
    settings = {row["key"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    return settings


def build_system_prompt(staff):
    role_desc = staff["role_description"]
    knowledge_base = staff["knowledge_base"]

    system_prompt = f"""你是一个AI客服员工，名叫"{staff['name']}"。
你的角色定位：{role_desc}

请始终以这个角色的身份和语气来回答用户的问题。保持专业、友好、耐心。"""

    # Add welcome message context
    welcome = staff.get("welcome_message", "")
    if welcome:
        system_prompt += f"\n\n你的开场白是：{welcome}（仅用于首次对话时）"

    if knowledge_base and knowledge_base != "[]":
        try:
            kb = json.loads(knowledge_base) if isinstance(knowledge_base, str) else knowledge_base
            if isinstance(kb, list) and len(kb) > 0:
                kb_text = "\n".join(kb)
                system_prompt += f"\n\n以下是你的知识库，请在回答时参考这些内容：\n{kb_text}"
            elif isinstance(kb, str) and kb.strip():
                lines = kb.strip().split("\n")
                kb_text = "\n".join(lines)
                system_prompt += f"\n\n以下是你的知识库，请在回答时参考这些内容：\n{kb_text}"
        except (json.JSONDecodeError, TypeError):
            if isinstance(knowledge_base, str) and knowledge_base.strip():
                lines = knowledge_base.strip().split("\n")
                kb_text = "\n".join(lines)
                system_prompt += f"\n\n以下是你的知识库，请在回答时参考这些内容：\n{kb_text}"

    return system_prompt


def check_transfer_keywords(staff_id: int, message: str) -> dict:
    """Check if message contains transfer-to-human keywords"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT transfer_keywords, transfer_message FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    conn.close()

    if not staff:
        return {"should_transfer": False, "message": ""}

    keywords_str = staff["transfer_keywords"] or "[]"
    transfer_msg = staff["transfer_message"] or "正在为您转接人工客服，请稍候..."

    try:
        keywords = json.loads(keywords_str)
    except (json.JSONDecodeError, TypeError):
        keywords = []

    if not keywords:
        return {"should_transfer": False, "message": ""}

    message_lower = message.lower().strip()
    for kw in keywords:
        if kw.strip() and kw.strip().lower() in message_lower:
            return {"should_transfer": True, "message": transfer_msg}

    return {"should_transfer": False, "message": ""}


def check_auto_reply(staff_id: int, message: str) -> dict:
    """Check if message matches auto-reply rules"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT auto_reply_rules FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    conn.close()

    if not staff:
        return {"matched": False, "reply": ""}

    rules_str = staff["auto_reply_rules"] or "[]"
    try:
        rules = json.loads(rules_str)
    except (json.JSONDecodeError, TypeError):
        rules = []

    if not rules:
        return {"matched": False, "reply": ""}

    message_lower = message.lower().strip()

    for rule in rules:
        keywords = rule.get("keywords", [])
        reply = rule.get("reply", "")
        match_type = rule.get("match_type", "contains")

        if not keywords or not reply:
            continue

        for kw in keywords:
            kw_lower = kw.strip().lower()
            if not kw_lower:
                continue
            if match_type == "exact":
                if message_lower == kw_lower:
                    return {"matched": True, "reply": reply}
            else:  # contains
                if kw_lower in message_lower:
                    return {"matched": True, "reply": reply}

    return {"matched": False, "reply": ""}


def filter_sensitive_words(staff_id: int, text: str) -> str:
    """Replace sensitive words with ***"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sensitive_words FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    conn.close()

    if not staff:
        return text

    words_str = staff["sensitive_words"] or "[]"
    try:
        words = json.loads(words_str)
    except (json.JSONDecodeError, TypeError):
        words = []

    if not words:
        return text

    result = text
    for word in words:
        word = word.strip()
        if word:
            result = result.replace(word, "***")

    return result


async def chat_with_ai(staff_id: int, session_id: str, user_message: str, conversation_id: int = None):
    conn = get_db()
    cursor = conn.cursor()

    # Get staff info
    cursor.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    if not staff:
        conn.close()
        raise ValueError(f"Staff with id {staff_id} not found")

    staff_dict = dict(staff)
    system_prompt = build_system_prompt(staff_dict)

    # Get or create conversation
    if conversation_id:
        cursor.execute("SELECT * FROM conversation WHERE id = ?", (conversation_id,))
        conv = cursor.fetchone()
    else:
        cursor.execute(
            "SELECT * FROM conversation WHERE staff_id = ? AND session_id = ?",
            (staff_id, session_id)
        )
        conv = cursor.fetchone()

    if conv:
        messages = json.loads(conv["messages"])
        conv_id = conv["id"]
    else:
        messages = []
        # Send welcome message on first interaction
        welcome = staff_dict.get("welcome_message", "")
        if welcome:
            messages.append({"role": "assistant", "content": welcome})

        admin_id = staff_dict.get("admin_id", 0)
        cursor.execute(
            "INSERT INTO conversation (admin_id, staff_id, session_id, messages) VALUES (?, ?, ?, ?)",
            (admin_id, staff_id, session_id, "[]")
        )
        conn.commit()
        conv_id = cursor.lastrowid

    # Add user message
    messages.append({"role": "user", "content": user_message})

    # Get settings (use the staff owner's admin_id)
    admin_id = staff_dict.get("admin_id", 0)
    settings = get_settings(admin_id)
    api_key = settings.get("api_key", ARK_API_KEY)
    model_id = settings.get("model_id", MODEL_ID)
    api_base_url = settings.get("api_base_url", API_BASE_URL)

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(messages)

    # Call DOUBAO API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": api_messages,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            result = response.json()
            ai_reply = result["choices"][0]["message"]["content"]
    except Exception as e:
        ai_reply = f"抱歉，AI服务暂时不可用，请稍后再试。(错误: {str(e)})"

    # Add AI reply to messages
    messages.append({"role": "assistant", "content": ai_reply})

    # Update conversation
    cursor.execute(
        "UPDATE conversation SET messages = ? WHERE id = ?",
        (json.dumps(messages, ensure_ascii=False), conv_id)
    )
    conn.commit()
    conn.close()

    return {
        "reply": ai_reply,
        "session_id": session_id,
        "staff_id": staff_id,
        "conversation_id": conv_id
    }
