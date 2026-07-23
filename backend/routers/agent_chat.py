"""智能体对话API - 前端智能体直接调用LLM，支持图片上传"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid

router = APIRouter()


class AgentChatRequest(BaseModel):
    role: str
    custom_prompt: Optional[str] = ""
    messages: List[dict] = []
    session_id: Optional[str] = ""
    images: Optional[List[str]] = []  # base64 data URLs


class AgentChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/agent-chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """智能体对话接口，支持多模态（图片+文字）"""
    from skills.llm_client import chat_completion, vision_completion, LLM_VL_MODEL
    import httpx, os

    has_images = bool(request.images)

    # Build system prompt
    system_prompt = f"你是一个专业的AI智能助手。\n\n你的角色定位：{request.role}"
    if request.custom_prompt:
        system_prompt += f"\n\n详细设定：{request.custom_prompt}"
    system_prompt += "\n\n请以这个角色身份回答用户问题，保持专业、友好。回答简洁实用，不要废话。支持Markdown格式。"
    if has_images:
        system_prompt += "\n\n用户发送了图片，请仔细分析图片内容并结合文字一起回答。"

    if has_images:
        # Multi-modal: use vision model
        # Build multi-modal messages
        api_messages = [{"role": "system", "content": system_prompt}]
        
        # Add previous text messages as context
        for msg in request.messages[-10:]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the latest user message with images
        last_user_content = []
        # Add images
        for img_data_url in request.images:
            last_user_content.append({
                "type": "image_url",
                "image_url": {"url": img_data_url}
            })
        # Add text from last message if exists
        last_msg = request.messages[-1] if request.messages else None
        text_content = last_msg["content"] if (last_msg and last_msg.get("role") == "user") else "请分析这张图片"
        last_user_content.append({"type": "text", "text": text_content})
        
        api_messages.append({"role": "user", "content": last_user_content})

        try:
            LLM_API_KEY = os.getenv("LLM_API_KEY", "")
            LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            
            payload = {
                "model": LLM_VL_MODEL,
                "messages": api_messages,
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{LLM_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                    json=payload
                )
                resp.raise_for_status()
                reply = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"抱歉，图片分析暂时不可用，请稍后再试。\n\n错误信息：{str(e)}"
    else:
        # Text-only: use regular model
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in request.messages[-20:]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            reply = await chat_completion(
                messages=api_messages,
                temperature=0.7,
                max_tokens=1500
            )
        except Exception as e:
            reply = f"抱歉，AI服务暂时不可用，请稍后再试。\n\n错误信息：{str(e)}"

    session_id = request.session_id or str(uuid.uuid4())[:12]

    return AgentChatResponse(reply=reply, session_id=session_id)
