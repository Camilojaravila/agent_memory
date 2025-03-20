from pydantic import BaseModel
from typing import List
from uuid import UUID

class ChatRequest(BaseModel):
    session_id: str
    user_input: str

class ChatResponse(BaseModel):
    assistant_response: str
    nodes: List[dict]

class SessionList(BaseModel):
    session_ids: List[UUID]