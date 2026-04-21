"""Dispatcher agent — routes planned tasks to the correct execution backend."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import TaskType

logger = logging.getLogger(__name__)


class DispatcherAgent:
    """Decide which execution backend should handle a task."""

    ROUTING_TABLE: dict[TaskType, str] = {
        TaskType.CODE_GENERATION: "devin",
        TaskType.REPO_ANALYSIS: "github+devin",
        TaskType.BUG_FIX: "devin",
        TaskType.REFACTORING: "devin",
        TaskType.AUTOMATION_SCRIPT: "devin",
        TaskType.DEPLOYMENT_SETUP: "devin",
        TaskType.AI_AGENT_CREATION: "devin",
    }

    def dispatch(self, plan: dict[str, Any]) -> dict[str, Any]:
        task_type = TaskType(plan["task_type"])
        backend = self.ROUTING_TABLE.get(task_type, "devin")
        needs_github = "github" in backend
        result = {
            "backend": backend,
            "needs_github": needs_github,
            "plan": plan,
        }
        logger.info(
            "Dispatching task_type=%s to backend=%s (github=%s)",
            task_type.value,
            backend,
            needs_github,
        )
        return result
