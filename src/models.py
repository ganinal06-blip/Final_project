from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AllowedUser(Base):
    __tablename__ = "allowed_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_identifier = Column(String, index=True, unique=True)
    created_at = Column(DateTime, server_default=func.now())

class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String)
    user_identifier = Column(String)
    action = Column(String)
    timestamp = Column(DateTime, server_default=func.now())
    reason = Column(String, nullable=True)

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, index=True)
    user_id = Column(String, index=True)
    username = Column(String, nullable=True)
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())