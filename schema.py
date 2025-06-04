from pydantic import BaseModel
from typing import List, Optional, Union, Literal
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
    feedback: List[str]
    observations: Optional[str]


class NewSession(BaseModel):
    session_id: str
    user_id: str


class ConversationHistory(BaseModel):
    message_id: Optional[Union[UUID, str]]
    session_id: Union[UUID, str]
    user_id: Union[UUID, str]
    content: str
    type: Literal['human', 'ai']
    created_at: Optional[datetime]
    like: bool
    feedback: List[str]
    observations: str

class Message(MessageUpdate):
    created_at: datetime


class Validation(BaseModel):
    user_id: Union[UUID, str]
    num_msg: int
    interval: str
    total_msg: int
    msg_left: int
    valid: int
