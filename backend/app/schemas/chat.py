from datetime import datetime
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime