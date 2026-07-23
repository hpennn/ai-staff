"""智能体对话API - 前端智能体直接调用LLM"""
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


class AgentChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/agent-chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """智能体对话接口"""
    from skills.llm_client import chat_completion
    import os

    # Build system prompt
    system_prompt = f"你是一个专业的AI智能助手。\n\n你的角色定位：{request.role}"
    if request.custom_prompt:
        system_prompt += f"\n\n详细设定：{request.custom_prompt}"
    system_prompt += "\n\n请以这个角色身份回答用户问题，保持专业、友好。回答简洁实用，不要废话。支持Markdown格式。"

    # Build messages for LLM
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages[-20:]:  # Keep last 20 messages for context
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
