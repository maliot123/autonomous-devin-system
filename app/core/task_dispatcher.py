"""Dispatch incoming tasks to the appropriate processing pipeline."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.config import TaskStatus, TaskType
from app.core.message_bus import message_bus
from app.database.db import get_db
from app.database.models import Task

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

TASK_ROUTING: dict[TaskType, str] = {
    TaskType.CODE_GENERATION: "devin",
    TaskType.REPO_ANALYSIS: "github+devin",
    TaskType.BUG_FIX: "devin",
    TaskType.REFACTORING: "devin",
    TaskType.AUTOMATION_SCRIPT: "devin",
    TaskType.DEPLOYMENT_SETUP: "devin",
    TaskType.AI_AGENT_CREATION: "devin",
}


async def dispatch_task(task: Task) -> None:
    """Route *task* to the correct execution backend and update its status."""
    route = TASK_ROUTING.get(TaskType(task.task_type), "devin")
    logger.info("Dispatching task %s via route '%s'", task.task_id, route)

    db = get_db()
    db.update_task_status(task.task_id, TaskStatus.QUEUED)
    await message_bus.publish(
        "task.queued", task_id=task.task_id, route=route
    )
