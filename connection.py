from postgres_db import get_db_engine
import models
from sqlalchemy.orm import Session
from typing import List, Dict
from sqlalchemy import text


def get_sessions_by_user(user_id: str) -> List[models.UserSession]:
    engine = get_db_engine()
    with Session(engine) as session:
        query = session.query(
            models.UserSession
        ).filter(
            models.UserSession.user_id == user_id,
            models.UserSession.is_active
        ).order_by(
            models.UserSession.updated_at.desc()
        )
        return query.all()

def get_session_user(session_id: str) -> models.UserSession:
    engine = get_db_engine()
    with Session(engine) as session:
        query = session.query(
            models.UserSession
        ).filter(
            models.UserSession.session_id == session_id,
            models.UserSession.is_active
        )
        return query.first()

    
def create_session(data: dict) -> models.UserSession:
    engine = get_db_engine()
    with Session(engine) as db:  # Use Session directly in a context manager
        db_new = models.UserSession(**data)
        db.add(db_new)
        db.commit()
        db.refresh(db_new)

    return db_new


def update_user_session(session_id: str, info: dict) -> models.UserSession:
    engine = get_db_engine()
    with Session(engine) as session:
        query = session.query(
            models.UserSession
        ).filter(
            models.UserSession.session_id == session_id
        )
        if query.first():
            query.update(info)
            session.commit()

        return query.first()

def create_message_revision(data: dict) -> models.MessageInfo:
    engine = get_db_engine()
    msg_id = data['message_id']
    with Session(engine) as db:  # Use Session directly in a context manager
        query = db.query(
            models.MessageInfo
        ).filter(
            models.MessageInfo.message_id == msg_id
        )
        if query.first():
            query.update(data)
            db.commit()
            return query.first()
        else:
            db_new = models.MessageInfo(**data)
            db.add(db_new)
            db.commit()
            db.refresh(db_new)

            return db_new

def get_message_revision(message_id: list) -> List[models.MessageInfo]:
    engine = get_db_engine()
    with Session(engine) as session:
        query = session.query(
            models.MessageInfo
        ).filter(
            models.MessageInfo.message_id.in_(message_id)
        )

        return query.all()
    
def count_chat_history_rows(session_ids: list[str], first_date) -> dict[str, int]:
    """
    Counts rows in 'chat_history' for each session_id using raw SQL.
    
    Args:
        session_ids (list[str]): List of session IDs to filter by.
        engine: SQLAlchemy engine (from create_engine).
    
    Returns:
        dict[str, int]: {session_id: row_count} (e.g., {"abc123": 5}).
    """
    if not session_ids:
        return {}

    # Convert session_ids to a tuple for SQL IN clause
    ids_tuple = tuple(session_ids)
    
    # Handle single-element tuple edge case (SQL requires trailing comma)
    if len(ids_tuple) == 1:
        ids_tuple = f"('{ids_tuple[0]}')"

    sql = text(f"""
        SELECT COUNT(*) as row_count
        FROM chat_history
        WHERE session_id IN {ids_tuple}
        AND created_at > '{first_date}'
    """)

    engine = get_db_engine()
    with Session(engine) as session:
        result = session.execute(sql)
        return [row.row_count for row in result]