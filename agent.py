from typing import Dict, List
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableMap
#from alloy_db import get_by_session_id, checkpoint
from prompts import prompt
from langchain_core.output_parsers import StrOutputParser
from postgres_db import get_by_session_id, checkpoint
from weaviate_db import get_weaviate_retriever
from uuid import uuid4


# Define the Gemini model
llm = ChatVertexAI(
                model="gemini-2.0-flash-exp",
                temperature=0,
                max_tokens=None,
                max_retries=6,
                stop=None
            )

llm_json_mode = ChatVertexAI(
                model="gemini-2.0-flash-exp",
                temperature=0,
                max_tokens=None,
                max_retries=6,
                stop=None
            )

embeddings = VertexAIEmbeddings(model_name="text-embedding-004")

# Get retriever
retriever = get_weaviate_retriever(embeddings)

def safe_query(x):
    question = x["question"]
    if isinstance(question, list):
        return retriever.invoke(question[-1].content)
    elif hasattr(question, "content"):
        return retriever.invoke(question.content)
    else:
        return retriever.invoke(question)

# Define a simple input mapping: gets context docs and passes to prompt
rag_chain = (
    RunnableMap({
        "context": safe_query,
        "question": lambda x: x["question"],
    })
    | prompt
    | llm
    | StrOutputParser()
)

chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    get_by_session_id,
    input_messages_key="question",
)


def call_model(message: str, session_id: str) -> list[BaseMessage]:
    config = {"configurable": {"thread_id": session_id}}
    msg_id = str(uuid4())
    input_message = HumanMessage(content=message, id=msg_id)
    ai_message: AIMessage = chain_with_history.invoke({"question": input_message}, config)
    return ai_message

def get_chat_messages(session_id: str) -> List[BaseMessage]:
    """Retrieves the chat history messages from Postgres based on session_id."""
    chat_history = get_by_session_id(session_id)
    return chat_history.messages