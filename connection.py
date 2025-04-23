from postgres_db import get_db_engine
import models
from sqlalchemy.orm import Session
from typing import List, Dict


def get_sessions_by_user(user_id: str) -> List[models.UserSession]:
    engine = get_db_engine()
    with Session(engine) as session:
        query = session.query(
            models.UserSession.session_id
        ).filter(
            models.UserSession.user_id == user_id,
            models.UserSession.is_active
        )
        return query.all()


    
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
    with Session(engine) as db:  # Use Session directly in a context manager
        db_new = models.MessageInfo(**data)
        db.add(db_new)
        db.commit()
        db.refresh(db_new)

    return db_new