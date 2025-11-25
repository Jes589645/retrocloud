from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    max_sessions_per_vm = Column(Integer, default=1)


class GameVM(Base):
    __tablename__ = "game_vms"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String, unique=True, index=True)
    status = Column(String, default="starting")  # starting, running, stopped
    current_sessions = Column(Integer, default=0)
    max_sessions = Column(Integer, default=1)
    last_activity = Column(DateTime, default=datetime.utcnow)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    vm_id = Column(Integer, ForeignKey("game_vms.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    streaming_url = Column(String, nullable=True)

    user = relationship("User")
    game = relationship("Game")
    vm = relationship("GameVM")
