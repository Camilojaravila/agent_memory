import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.messages import BaseMessage
from typing import List
from sqlalchemy import create_engine, text
from models import create_tables
from configs import get_secret


secret_name = os.environ.get("DB_SECRET_NAME")
db_settings: dict = get_secret(secret_name)
env_name = os.environ.get("ENV")
host = db_settings.get('POSTGRES_HOST') if env_name == 'local' else db_settings.get('POSTGRES_HOST_PRIVATE') 


DB_URI = f"postgresql://{db_settings.get('POSTGRES_USER')}:{db_settings.get('POSTGRES_PASSWORD')}@{host}:{db_settings.get('POSTGRES_PORT')}/{db_settings.get('POSTGRES_DB')}"
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

table_name = db_settings.get('TABLE_HISTORY_NAME')

db_pool = ConnectionPool(
    conninfo=DB_URI,
    min_size=1,
    max_size=10,
    kwargs=connection_kwargs
)


checkpoint = PostgresSaver(db_pool)


def init_tables():
    """
    Initialize the tables to store for the checkpoint, the Message history and the Vector Store (not implemented)
    
    Uses env variables of TABLE_CHECKPOINT_NAME, TABLE_HISTORY_NAME, TABLE_VECTOR_NAME
    """
    checkpoint.setup()
    
    db_conn = next(get_db())
    try:
        PostgresChatMessageHistory.create_tables(db_conn, table_name)
    finally:
        db_conn.close()
    engine = get_db_engine()
    create_tables(engine)




class PostgresChatHistory():
    """Postgres-backed chat message history using LangChain's PostgresChatMessageHistory."""

    def __init__(self, session_id:str):
        # Consider applying the connection_string fix to init_memory if not already done
        history = init_memory(session_id)
        self.chat_history = history
        self.session_id = session_id

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Stores messages in the Postgres database"""
        # Now, call the underlying standard method
        try:
            # Note: The standard PostgresChatMessageHistory doesn't have add_messages (plural)
            # It has add_message (singular). The checkpointer likely calls add_message repeatedly.
            # If LangGraph calls your wrapper's add_messages (plural), you need the loop.
            # If LangGraph somehow calls the underlying add_message directly, this wrapper method might not even be hit by the checkpointer.
            # Let's assume for now your wrapper *is* somehow involved or you call it manually.
            # A more direct test might involve subclassing PostgresChatMessageHistory itself.
            for message in messages:
                self.chat_history.add_message(message) # Call standard add_message

        except Exception as e:
            print(f"Error during self.chat_history.add_message: {e}")
            import traceback
            traceback.print_exc()


    def get_messages(self) -> List[BaseMessage]:
        """Retrieves messages from the database"""
        return self.chat_history.messages # Use the property

    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieves messages from the database."""
        # Call the underlying get_messages method or messages property
        try:
            # The standard class uses the .messages property primarily
            return self.chat_history.messages
        except Exception as e:
            print(f"Error during self.chat_history.messages: {e}")
            return []


    def clear(self) -> None:
        """Deletes chat history for a session"""
        self.chat_history.clear()


def get_by_session_id(session_id: str) -> PostgresChatHistory:
    """Retrieve chat history from Postgres based on session_id."""
    return PostgresChatHistory(session_id=session_id)

def get_db():
    """Yields a persistent database connection from the pool."""
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)  # Return connection to the pool instead of closing it

def init_memory(session_id: str) -> PostgresChatMessageHistory:
    """Retrieve chat history for a session using a raw connection."""
    db_conn = next(get_db())

    # Initialize the chat history manager
    chat_history = PostgresChatMessageHistory(
        table_name,
        session_id,
        sync_connection=db_conn
    )
    return chat_history

def get_db_engine():
    """Creates a SQLAlchemy engine for database operations."""

    return create_engine(DB_URI)

def get_all_sessions():
    db_conn = next(get_db())
    """Retrieve all unique session_ids from the chat history table."""

    query = f"SELECT DISTINCT session_id FROM {table_name};"
    with db_conn.cursor() as cursor:
        cursor.execute(query)
        session_ids = [row[0] for row in cursor.fetchall()]

    return session_ids

#init_tables()