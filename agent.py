from typing import Dict, List
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
import postgres_db


"""
# Load the service account key file
with open("niilo-441811-032714d1b5e6.json", "r") as f:
    service_account_info = json.load(f)

# Create credentials
credentials = service_account.Credentials.from_service_account_info(
    service_account_info
)
"""

# Define the Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1
)

llm_json_mode = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1,
    format="json"
)

class PostgresChatHistory():
    """Postgres-backed chat message history using LangChain's PostgresChatMessageHistory."""

    def __init__(self, session_id:str):
        history = postgres_db.init_memory(session_id)
        self.chat_history = history

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Stores messages in the Postgres database"""
        for message in messages:
            self.chat_history.add_message(message)

    def get_messages(self) -> List[BaseMessage]:
        """Retrieves messages from the database"""
        return self.chat_history.messages
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieves messages from the database."""
        return self.chat_history.get_messages()  # Ensure it returns a list of BaseMessage objects

    def clear(self) -> None:
        """Deletes chat history for a session"""
        self.chat_history.clear()


def get_by_session_id(session_id: str) -> PostgresChatHistory:
    """Retrieve chat history from Postgres based on session_id."""
    return PostgresChatHistory(session_id=session_id)

chain_with_history = RunnableWithMessageHistory(
    llm,
    # Uses the get_by_session_id function defined in the example
    # above.
    get_by_session_id,
)


def call_model(message: str, session_id: str) -> list[BaseMessage]:
    # RunnableWithMessageHistory takes care of reading the message history
    # and updating it with the new human message and ai response.
    config = {"configurable": {"session_id": session_id}}
    input_message = HumanMessage(message)
    ai_message: AIMessage = chain_with_history.invoke(input_message, config)

    return ai_message

def get_session_ids():
    return postgres_db.get_all_sessions()

def get_chat_messages(session_id: str) -> List[BaseMessage]:
    """Retrieves the chat history messages from Postgres based on session_id."""
    chat_history = get_by_session_id(session_id)
    return chat_history.messages