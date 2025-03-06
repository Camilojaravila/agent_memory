from pydantic import BaseModel
from typing import Annotated
from langchain_core.messages import HumanMessage, AIMessage

class ChatRequest(BaseModel):
    message: str
