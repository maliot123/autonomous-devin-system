"""Database access layer wrapping SQLAlchemy sessions."""

from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import TaskStatus, get_settings
from app.database.models import Agent, Base, ExecutionLog, Repository, Task

logger = logging.getLogger(__name__)

_session_factory: Optional[sessionmaker] = None  # type: ignore[type-arg]
_engine = None


def init_db(database_url: Optional[str] = None) -> None:
    """Initialise the database engine and create tables if needed."""
    global _session_factory, _engine

    url = database_url or get_settings().database_url

    if url.startswith("sqlite:///./"):
        db_path = url.replace("sqlite:///./", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    _engine = create_engine(url, echo=False, future=True)
    Base.metadata.create_all(_engine)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    logger.info("Database initialised: %s", url)


def _get_session() -> Session:
    if _session_factory is None:
        init_db()
    assert _session_factory is not None
    return _session_factory()


class DatabaseManager:
    """Convenience wrapper around common DB operations."""

    # --- Tasks -----------------------------------------------------------

    def create_task(self, **kwargs: object) -> Task:
        with _get_session() as session:
            task = Task(**kwargs)
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info("Created task %s", task.task_id)
            return task

    def get_task(self, task_id: str) -> Optional[Task]:
        with _get_session() as session:
            return session.query(Task).filter_by(task_id=task_id).first()

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
        devin_job_id: Optional[str] = None,
    ) -> Optional[Task]:
        with _get_session() as session:
            task = session.query(Task).filter_by(task_id=task_id).first()
            if task is None:
                return None
            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if devin_job_id is not None:
                task.devin_job_id = devin_job_id
            session.commit()
            session.refresh(task)
            return task

    def claim_task(self, task_id: str) -> bool:
        """Atomically transition a task from QUEUED to IN_PROGRESS.

        Returns ``True`` if the claim succeeded (the task was still QUEUED),
        ``False`` otherwise (already claimed by another worker).
        """
        with _get_session() as session:
            stmt = (
                update(Task)
                .where(Task.task_id == task_id, Task.status == TaskStatus.QUEUED)
                .values(status=TaskStatus.IN_PROGRESS)
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount > 0

    def list_tasks(
        self, status: Optional[TaskStatus] = None, limit: int = 50
    ) -> list[Task]:
        with _get_session() as session:
            q = session.query(Task)
            if status:
                q = q.filter_by(status=status)
            return list(q.order_by(Task.created_at.desc()).limit(limit).all())

    # --- Repositories ----------------------------------------------------

    def add_repository(self, **kwargs: object) -> Repository:
        with _get_session() as session:
            repo = Repository(**kwargs)
            session.add(repo)
            session.commit()
            session.refresh(repo)
            return repo

    def get_repository_by_url(self, url: str) -> Optional[Repository]:
        with _get_session() as session:
            return session.query(Repository).filter_by(url=url).first()

    # --- Execution Logs --------------------------------------------------

    def add_log(self, **kwargs: object) -> ExecutionLog:
        with _get_session() as session:
            log = ExecutionLog(**kwargs)
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

    def get_logs(
        self, task_id: Optional[str] = None, limit: int = 100
    ) -> list[ExecutionLog]:
        with _get_session() as session:
            q = session.query(ExecutionLog)
            if task_id:
                q = q.filter_by(task_id=task_id)
            return list(q.order_by(ExecutionLog.created_at.desc()).limit(limit).all())

    # --- Agents ----------------------------------------------------------

    def register_agent(self, name: str, agent_type: str) -> Agent:
        with _get_session() as session:
            agent = session.query(Agent).filter_by(name=name).first()
            if agent:
                agent.agent_type = agent_type
            else:
                agent = Agent(name=name, agent_type=agent_type)
                session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def list_agents(self) -> list[Agent]:
        with _get_session() as session:
            return list(session.query(Agent).all())

    def update_agent_status(self, name: str, status: str) -> Optional[Agent]:
        with _get_session() as session:
            agent = session.query(Agent).filter_by(name=name).first()
            if agent is None:
                return None
            agent.status = status
            session.commit()
            session.refresh(agent)
            return agent


_db_instance: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Return the global :class:`DatabaseManager` singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
