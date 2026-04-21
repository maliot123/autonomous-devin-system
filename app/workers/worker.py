"""Background task worker using Redis + RQ (or database-polling fallback)."""

from __future__ import annotations

import asyncio
import logging
import time

from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.planner_agent import PlannerAgent
from app.core.config import TaskStatus, get_settings
from app.database.db import get_db, init_db

logger = logging.getLogger(__name__)


def enqueue_task(task_id: str) -> None:
    """Add a task to the processing queue.

    Attempts to use Redis (via ``rq``) first.  Falls back to marking the
    task as QUEUED in the database so the worker can pick it up by polling.
    """
    db = get_db()
    db.update_task_status(task_id, TaskStatus.QUEUED)

    settings = get_settings()
    try:
        from redis import Redis
        from rq import Queue

        conn = Redis.from_url(settings.redis_url)
        conn.ping()
        q = Queue(connection=conn)
        q.enqueue(_process_task_sync, task_id)
        logger.info("Task %s enqueued via Redis/RQ", task_id)
    except Exception:
        logger.warning("Redis unavailable — worker will pick up task via DB polling")


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
    """Poll the database for QUEUED tasks and process them.

    In production with Redis available, use ``rq worker`` instead.
    When Redis is down, the API marks tasks as QUEUED in the database
    and this loop picks them up — works across separate processes.
    """
    init_db()
    logger.info("Worker started (database-polling mode)")
    while True:
        db = get_db()
        queued_tasks = db.list_tasks(status=TaskStatus.QUEUED, limit=10)
        for task in queued_tasks:
            logger.info("Picking up queued task %s from database", task.task_id)
            try:
                asyncio.run(_process_task(task.task_id))
            except Exception:
                logger.exception("Worker error processing task %s", task.task_id)
        time.sleep(2)
