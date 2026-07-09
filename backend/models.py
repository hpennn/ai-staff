from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    staff_id: int
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    staff_id: int


class StaffCreate(BaseModel):
    name: str
    role_description: str
    knowledge_base: Optional[str] = ""
    avatar_color: Optional[str] = "#6366f1"


class StaffResponse(BaseModel):
    id: int
    name: str
    role_description: str
    knowledge_base: str
    avatar_color: str
    created_at: str


class ConversationResponse(BaseModel):
    id: int
    staff_id: int
    staff_name: Optional[str] = ""
    session_id: str
    last_message: Optional[str] = ""
    avatar_color: Optional[str] = "#6366f1"
    created_at: str


class ConversationDetailResponse(BaseModel):
    id: int
    staff_id: int
    session_id: str
    messages: list
    created_at: str


class SettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    api_base_url: Optional[str] = None


class SettingsResponse(BaseModel):
    api_key: str
    model_id: str
    api_base_url: str


class WebhookPayload(BaseModel):
    platform: str
    staff_id: int
    message: str
    session_id: Optional[str] = "webhook-default"
