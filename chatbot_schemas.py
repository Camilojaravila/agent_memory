from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import add_messages


# Schema for structured output to use as routing logic
class Route(BaseModel):
    step: Literal["formula", "chatbot"] = Field(
        None, description="The next step in the routing process"
    )

class Formula(BaseModel):
    key: str
    name: str
    is_calculated: bool
    params: List[str]


class List_Formula(BaseModel):
    formulas: List[Formula]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    decision: str
    formulas: Optional[List[Formula]] = None  # Add this line