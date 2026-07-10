from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse
from agent_service import chat_with_ai, check_transfer_keywords, check_auto_reply, filter_sensitive_words
import json

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    try:
        # Filter sensitive words from user message first
        filtered_message = filter_sensitive_words(request.staff_id, request.message)

        # Check transfer keywords
        transfer_result = check_transfer_keywords(request.staff_id, filtered_message)
        if transfer_result["should_transfer"]:
            return ChatResponse(
                reply=transfer_result["message"],
                session_id=request.session_id,
                staff_id=request.staff_id
            )

        # Check auto reply rules
        auto_reply = check_auto_reply(request.staff_id, filtered_message)
        if auto_reply["matched"]:
            # Still save to conversation
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversation WHERE staff_id = ? AND session_id = ?",
                (request.staff_id, request.session_id)
            )
            conv = cursor.fetchone()
            if conv:
                messages = json.loads(conv["messages"])
                conv_id = conv["id"]
            else:
                messages = []
                cursor.execute(
                    "INSERT INTO conversation (staff_id, session_id, messages) VALUES (?, ?, ?)",
                    (request.staff_id, request.session_id, "[]")
                )
                conn.commit()
                conv_id = cursor.lastrowid

            messages.append({"role": "user", "content": filtered_message})
            messages.append({"role": "assistant", "content": auto_reply["reply"]})
            cursor.execute(
                "UPDATE conversation SET messages = ? WHERE id = ?",
                (json.dumps(messages, ensure_ascii=False), conv_id)
            )
            conn.commit()
            conn.close()

            return ChatResponse(
                reply=auto_reply["reply"],
                session_id=request.session_id,
                staff_id=request.staff_id
            )

        # Normal AI chat
        result = await chat_with_ai(
            staff_id=request.staff_id,
            session_id=request.session_id,
            user_message=filtered_message
        )

        # Filter sensitive words from AI reply
        filtered_reply = filter_sensitive_words(request.staff_id, result["reply"])

        return ChatResponse(
            reply=filtered_reply,
            session_id=result["session_id"],
            staff_id=result["staff_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天服务异常: {str(e)}")
