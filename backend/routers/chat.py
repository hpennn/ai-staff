from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse
from agent_service import chat_with_ai

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    try:
        result = await chat_with_ai(
            staff_id=request.staff_id,
            session_id=request.session_id,
            user_message=request.message
        )
        return ChatResponse(
            reply=result["reply"],
            session_id=result["session_id"],
            staff_id=result["staff_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天服务异常: {str(e)}")
