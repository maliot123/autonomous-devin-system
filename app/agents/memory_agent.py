"""Memory agent — persists and retrieves task context and history."""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import TaskStatus
from app.database.db import get_db

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Provide a read-only view of system history for other agents."""

    def get_task_history(self, limit: int = 20) -> list[dict[str, Any]]:
        db = get_db()
        tasks = db.list_tasks(limit=limit)
        return [t.to_dict() for t in tasks]

    def get_task_context(self, task_id: str) -> Optional[dict[str, Any]]:
        db = get_db()
        task = db.get_task(task_id)
        if task is None:
            return None
        logs = db.get_logs(task_id=task_id)
        return {
            "task": task.to_dict(),
            "logs": [lg.to_dict() for lg in logs],
        }

    def get_active_tasks(self) -> list[dict[str, Any]]:
        db = get_db()
        active = db.list_tasks(status=TaskStatus.IN_PROGRESS)
        queued = db.list_tasks(status=TaskStatus.QUEUED)
        return [t.to_dict() for t in active + queued]

    def get_system_summary(self) -> dict[str, Any]:
        db = get_db()
        all_tasks = db.list_tasks(limit=1000)
        status_counts: dict[str, int] = {}
        for t in all_tasks:
            key = t.status.value if t.status else "unknown"
            status_counts[key] = status_counts.get(key, 0) + 1
        agents = db.list_agents()
        return {
            "total_tasks": len(all_tasks),
            "status_breakdown": status_counts,
            "agents": [a.to_dict() for a in agents],
        }
