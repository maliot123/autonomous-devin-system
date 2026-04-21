"""Planner agent — breaks down high-level requests into actionable task plans."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import TaskType

logger = logging.getLogger(__name__)

TASK_KEYWORD_MAP: dict[str, TaskType] = {
    "build": TaskType.CODE_GENERATION,
    "create": TaskType.CODE_GENERATION,
    "generate": TaskType.CODE_GENERATION,
    "analyze": TaskType.REPO_ANALYSIS,
    "review": TaskType.REPO_ANALYSIS,
    "fix": TaskType.BUG_FIX,
    "bug": TaskType.BUG_FIX,
    "debug": TaskType.BUG_FIX,
    "refactor": TaskType.REFACTORING,
    "clean": TaskType.REFACTORING,
    "script": TaskType.AUTOMATION_SCRIPT,
    "automate": TaskType.AUTOMATION_SCRIPT,
    "deploy": TaskType.DEPLOYMENT_SETUP,
    "setup": TaskType.DEPLOYMENT_SETUP,
    "agent": TaskType.AI_AGENT_CREATION,
}


class PlannerAgent:
    """Infer task type and build a structured task plan from natural language."""

    def plan(self, description: str, repository: str | None = None) -> dict[str, Any]:
        task_type = self._infer_task_type(description)
        steps = self._build_steps(task_type, description, repository)
        plan: dict[str, Any] = {
            "task_type": task_type.value,
            "description": description,
            "repository": repository,
            "steps": steps,
        }
        logger.info("Plan created: type=%s, steps=%d", task_type.value, len(steps))
        return plan

    def _infer_task_type(self, description: str) -> TaskType:
        lower = description.lower()
        for keyword, task_type in TASK_KEYWORD_MAP.items():
            if keyword in lower:
                return task_type
        return TaskType.CODE_GENERATION

    def _build_steps(
        self, task_type: TaskType, description: str, repository: str | None
    ) -> list[str]:
        base_steps = ["Analyze requirements", "Execute with Devin", "Validate output"]
        if repository:
            base_steps.insert(1, f"Clone and analyze repository: {repository}")
        if task_type == TaskType.DEPLOYMENT_SETUP:
            base_steps.append("Verify deployment configuration")
        if task_type == TaskType.BUG_FIX:
            base_steps.insert(1, "Reproduce and identify root cause")
        return base_steps
