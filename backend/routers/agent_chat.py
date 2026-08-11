"""智能体对话API - 前端智能体直接调用LLM，支持图片上传，含积分检查，支持SSE流式输出"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid

from credits_database import register_user, get_user_credits, deduct_credits

router = APIRouter()

# 积分消耗配置
CREDIT_COST_TEXT = 30    # 纯文字对话
CREDIT_COST_IMAGE = 50   # 含图片对话


class AgentChatRequest(BaseModel):
    role: str
    custom_prompt: Optional[str] = ""
    messages: List[dict] = []
    session_id: Optional[str] = ""
    images: Optional[List[str]] = []  # base64 data URLs
    user_id: Optional[str] = ""  # 设备ID，用于积分检查


class AgentChatResponse(BaseModel):
    reply: str
    session_id: str
    remaining_credits: int = -1


def _resolve_user_id(request_user_id: str, fastapi_request: Request) -> str:
    """从请求中解析有效的用户ID"""
    effective_user_id = request_user_id
    if fastapi_request:
        auth_header = fastapi_request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            from auth_database import verify_token
            user_info = verify_token(token)
            if user_info:
                effective_user_id = f"user_{user_info['user_id']}"
    return effective_user_id


def _build_system_prompt(role: str, custom_prompt: str, has_images: bool) -> str:
    system_prompt = f"你是一个专业的AI智能助手。\n\n你的角色定位：{role}"
    if custom_prompt:
        system_prompt += f"\n\n详细设定：{custom_prompt}"
    system_prompt += "\n\n请以这个角色身份回答用户问题，保持专业、友好。回答简洁实用，不要废话。支持Markdown格式。"
    if has_images:
        system_prompt += "\n\n用户发送了图片，请仔细分析图片内容并结合文字一起回答。"
    return system_prompt


async def _stream_text_reply(
    api_messages: list,
    temperature: float = 0.7,
    max_tokens: int = 1500,
):
    """流式输出纯文字回复的SSE生成器"""
    from skills.llm_client import chat_completion
    full_text = ""
    try:
        stream_gen = await chat_completion(
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream_gen:
            full_text += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_msg = f"抱歉，AI服务暂时不可用，请稍后再试。\n\n错误信息：{str(e)}"
        full_text = error_msg
        yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"
    # 结束标记 + 元数据
    yield f"data: {json.dumps({'done': True, 'full_text': full_text}, ensure_ascii=False)}\n\n"


async def _stream_vision_reply(api_messages: list):
    """流式输出视觉（图片+文字）回复的SSE生成器"""
    import httpx, os
    full_text = ""
    try:
        LLM_API_KEY = os.getenv("LLM_API_KEY", "")
        LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        from skills.llm_client import LLM_VL_MODEL

        payload = {
            "model": LLM_VL_MODEL,
            "messages": api_messages,
            "max_tokens": 2000,
            "temperature": 0.7,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                    elif line.startswith("data:"):
                        data_str = line[5:]
                    else:
                        continue
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_text += content
                                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    except (json.JSONDecodeError, KeyError):
                        continue
    except Exception as e:
        error_msg = f"抱歉，图片分析暂时不可用，请稍后再试。\n\n错误信息：{str(e)}"
        full_text = error_msg
        yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'done': True, 'full_text': full_text}, ensure_ascii=False)}\n\n"


@router.post("/agent-chat")
async def agent_chat(request: AgentChatRequest, fastapi_request: Request = None):
    """智能体对话接口（SSE流式输出），支持多模态（图片+文字），含积分检查"""
    # 优先使用Token认证获取user_id
    effective_user_id = _resolve_user_id(request.user_id, fastapi_request)

    has_images = bool(request.images)

    # ===== 积分检查（流式在开始前检查，结束后扣减） =====
    remaining_credits = -1
    if effective_user_id:
        register_user(effective_user_id)
        cost = CREDIT_COST_IMAGE if has_images else CREDIT_COST_TEXT
        credits = get_user_credits(effective_user_id)
        if credits < cost:
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "积分不足，请充值后继续使用",
                    "required": cost,
                    "remaining": credits,
                },
            )

    # Build system prompt
    system_prompt = _build_system_prompt(request.role, request.custom_prompt or "", has_images)

    session_id = request.session_id or str(uuid.uuid4())[:12]

    if has_images:
        # Multi-modal: use vision model
        api_messages = [{"role": "system", "content": system_prompt}]
        # Add previous text messages as context
        for msg in request.messages[-10:]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        # Add the latest user message with images
        last_user_content = []
        for img_data_url in request.images:
            last_user_content.append({
                "type": "image_url",
                "image_url": {"url": img_data_url}
            })
        last_msg = request.messages[-1] if request.messages else None
        text_content = last_msg["content"] if (last_msg and last_msg.get("role") == "user") else "请分析这张图片"
        last_user_content.append({"type": "text", "text": text_content})
        api_messages.append({"role": "user", "content": last_user_content})

        gen = _stream_vision_reply(api_messages)
    else:
        # Text-only: use regular model
        api_messages = [{"role": "system", "content": system_prompt}]
        for msg in request.messages[-20:]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        gen = _stream_text_reply(api_messages, temperature=0.7, max_tokens=1500)

    # 扣积分包装：流式完成后扣减，并在 done 事件中返回剩余积分
    async def _stream_with_credits():
        full_text = ""
        async for chunk in gen:
            # 检测 done 事件，追加积分信息
            if '"done": true' in chunk:
                try:
                    data_part = chunk[len("data: "):].strip()
                    if data_part.endswith("\n\n"):
                        data_part = data_part[:-2]
                    obj = json.loads(data_part)
                    full_text = obj.get("full_text", "")

                    # ===== 对话成功后扣积分 =====
                    remaining = -1
                    if effective_user_id:
                        cost = CREDIT_COST_IMAGE if has_images else CREDIT_COST_TEXT
                        cost_desc = "智能体对话(含图片)" if has_images else "智能体对话(文字)"
                        deduct_credits(effective_user_id, cost, cost_desc)
                        remaining = get_user_credits(effective_user_id)

                    obj["remaining_credits"] = remaining
                    obj["session_id"] = session_id
                    yield f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"
                    continue
                except Exception:
                    yield chunk
                    continue
            yield chunk

    # 返回 SSE 流式响应
    return StreamingResponse(
        _stream_with_credits(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
