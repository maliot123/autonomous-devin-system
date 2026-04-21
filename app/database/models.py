"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase

from app.core.config import TaskPriority, TaskStatus, TaskType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String(32), primary_key=True, default=_new_id)
    task_type = Column(Enum(TaskType), nullable=False)
    description = Column(Text, nullable=False)
    repository = Column(String(512), nullable=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.NORMAL)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    devin_job_id = Column(String(128), nullable=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    created_by = Column(String(128), nullable=True)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value if self.task_type else None,
            "description": self.description,
            "repository": self.repository,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "devin_job_id": self.devin_job_id,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }


class Repository(Base):
    __tablename__ = "repositories"

    repo_id = Column(String(32), primary_key=True, default=_new_id)
    url = Column(String(512), nullable=False, unique=True)
    name = Column(String(256), nullable=False)
    default_branch = Column(String(128), default="main")
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    analysis_result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self) -> dict:
        return {
            "repo_id": self.repo_id,
            "url": self.url,
            "name": self.name,
            "default_branch": self.default_branch,
            "last_analyzed_at": (
                self.last_analyzed_at.isoformat() if self.last_analyzed_at else None
            ),
            "analysis_result": self.analysis_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    log_id = Column(String(32), primary_key=True, default=_new_id)
    task_id = Column(String(32), nullable=True)
    level = Column(String(16), default="INFO")
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self) -> dict:
        return {
            "log_id": self.log_id,
            "task_id": self.task_id,
            "level": self.level,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String(32), primary_key=True, default=_new_id)
    name = Column(String(128), nullable=False, unique=True)
    agent_type = Column(String(64), nullable=False)
    status = Column(String(32), default="idle")
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type,
            "status": self.status,
            "last_active_at": (
                self.last_active_at.isoformat() if self.last_active_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
