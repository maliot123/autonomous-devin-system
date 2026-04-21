"""Background task worker using Redis + RQ (or in-process fallback)."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.planner_agent import PlannerAgent
from app.core.config import TaskStatus, get_settings
from app.database.db import get_db, init_db

logger = logging.getLogger(__name__)

# In-memory queue used when Redis is unavailable
_task_queue: list[str] = []


def enqueue_task(task_id: str) -> None:
    """Add a task to the processing queue.

    Attempts to use Redis (via ``rq``) first.  Falls back to an in-memory
    list that :func:`run_worker` drains.
    """
    settings = get_settings()
    try:
        from redis import Redis
        from rq import Queue

        conn = Redis.from_url(settings.redis_url)
        q = Queue(connection=conn)
        q.enqueue(_process_task_sync, task_id)
        logger.info("Task %s enqueued via Redis/RQ", task_id)
    except Exception:
        logger.warning("Redis unavailable — using in-memory queue")
        _task_queue.append(task_id)
        db = get_db()
        db.update_task_status(task_id, TaskStatus.QUEUED)


def _process_task_sync(task_id: str) -> None:
    """Synchronous wrapper so RQ can call into async execution."""
    asyncio.run(_process_task(task_id))


async def _process_task(task_id: str) -> None:
    """Process a single task end-to-end."""
    db = get_db()
    task = db.get_task(task_id)
    if task is None:
        logger.error("Task %s not found in database", task_id)
        return

    logger.info("Processing task %s (%s)", task_id, task.task_type)

    planner = PlannerAgent()
    dispatcher = DispatcherAgent()
    executor = ExecutionAgent()

    plan = planner.plan(task.description, task.repository)
    dispatch_info = dispatcher.dispatch(plan)

    prompt_parts = [f"Task: {task.description}"]
    if task.repository:
        prompt_parts.append(f"Repository: {task.repository}")
    prompt_parts.append(f"Task type: {task.task_type.value}")
    prompt = "\n".join(prompt_parts)

    result = await executor.execute(task_id, prompt)
    logger.info("Task %s finished with status=%s", task_id, result.get("status"))


def run_worker() -> None:
    """Run a simple polling worker that drains the in-memory queue.

    In production, use ``rq worker`` instead.
    """
    init_db()
    logger.info("Worker started (in-memory mode)")
    while True:
        if _task_queue:
            task_id = _task_queue.pop(0)
            try:
                asyncio.run(_process_task(task_id))
            except Exception:
                logger.exception("Worker error processing task %s", task_id)
        time.sleep(2)
