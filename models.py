from sqlalchemy import Column, Integer, String, ForeignKey, Uuid, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import func
import uuid
import datetime

Base = declarative_base()

class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    session_id = Column(Uuid, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class MessageInfo(Base):
    __tablename__ = 'message_revision'

    id = Column(Integer, primary_key=True)
    message_id = Column(String, nullable=False)
    like = Column(Boolean, default=True, nullable=False)
    feedback = Column(JSON, nullable=False)
    observations = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())



def create_tables(engine):
    """
    Creates all tables defined in this module in the database.
    """
    Base.metadata.create_all(engine) # Create the tables

