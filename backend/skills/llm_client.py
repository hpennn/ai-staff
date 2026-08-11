"""统一LLM客户端 - 支持OpenAI兼容接口，支持流式和非流式调用"""
import httpx
import os
import json
from typing import Optional, AsyncGenerator

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
LLM_VL_BASE_URL = os.getenv("LLM_VL_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
LLM_VL_API_KEY = os.getenv("LLM_VL_API_KEY", "")
LLM_VL_MODEL = os.getenv("LLM_VL_MODEL", "ep-20260707225043-z7nkm")


async def chat_completion(
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
    stream: bool = False,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str | AsyncGenerator[str, None]:
    """调用LLM获取文本回复

    当 stream=False（默认）时，返回完整文本字符串。
    当 stream=True 时，返回异步生成器，逐块 yield delta 文本。
    """
    _api_key = api_key or LLM_API_KEY
    _base_url = base_url or LLM_BASE_URL
    if not _api_key:
        if stream:
            async def _empty_gen():
                yield "[LLM未配置] 请设置 LLM_API_KEY 环境变量"
            return _empty_gen()
        return "[LLM未配置] 请设置 LLM_API_KEY 环境变量"

    payload = {
        "model": model or LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    if stream:
        payload["stream"] = True

    if stream:
        return _chat_stream(_base_url, _api_key, payload)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {_api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _chat_stream(base_url: str, api_key: str, payload: dict) -> AsyncGenerator[str, None]:
    """流式调用LLM，逐块 yield delta content 文本"""
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
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
                            yield content
                except (json.JSONDecodeError, KeyError):
                    continue


async def vision_completion(
    image_url: str,
    prompt: str,
    model: Optional[str] = None,
    stream: bool = False,
) -> str | AsyncGenerator[str, None]:
    """调用多模态LLM分析图片。支持流式。"""
    if not LLM_VL_API_KEY:
        if stream:
            async def _empty_gen():
                yield "[LLM未配置] 请设置 LLM_API_KEY 环境变量"
            return _empty_gen()
        return "[LLM未配置] 请设置 LLM_API_KEY 环境变量"

    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": prompt}
        ]
    }]

    payload = {
        "model": model or LLM_VL_MODEL,
        "messages": messages,
        "max_tokens": 2000,
    }
    if stream:
        payload["stream"] = True
        return _chat_stream(LLM_VL_BASE_URL, LLM_VL_API_KEY, payload)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{LLM_VL_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_VL_API_KEY}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def get_embedding(text: str, model: str = "text-embedding-v2") -> list:
    """获取文本embedding向量"""
    if not LLM_API_KEY:
        return [0.0] * 768

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={"model": model, "input": text}
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
