import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langchain_postgres import PostgresChatMessageHistory


load_dotenv('.env')

DB_URI = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

table_name = "chat_history"

db_pool = ConnectionPool(
    conninfo=DB_URI,
    min_size=1,
    max_size=10,
)

checkpoint = PostgresSaver(db_pool)

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


def get_all_sessions():
    db_conn = next(get_db())
    """Retrieve all unique session_ids from the chat history table."""
    query = "SELECT DISTINCT session_id FROM chat_history;"
    with db_conn.cursor() as cursor:
        cursor.execute(query)
        session_ids = [row[0] for row in cursor.fetchall()]
    return session_ids