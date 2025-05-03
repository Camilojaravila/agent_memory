from pydantic import BaseModel
from typing import List, Optional, Union
from uuid import UUID
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str
    user_input: str

class ChatResponse(BaseModel):
    assistant_response: str
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    nodes: List[dict]

class Session(BaseModel):
    session_id: Union[UUID, str]
    created_at: datetime
    last_update: datetime
    user_id: Union[UUID, str]
    first_message:  str

class SessionList(BaseModel):
    chats: List[Session]


class MessageUpdate(BaseModel):
    message_id: str
    like: bool = True,
    feedbacks: List[str]
    observations: Optional[str]