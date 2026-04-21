"""Execution agent — sends work to Devin and monitors progress."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import TaskStatus
from app.database.db import get_db
from app.integrations.devin_client import get_devin_client

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """Create a Devin session for a task and poll until completion."""

    async def execute(self, task_id: str, prompt: str) -> dict[str, Any]:
        db = get_db()
        client = get_devin_client()

        db.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        db.add_log(task_id=task_id, level="INFO", message="Starting Devin session")

        try:
            session = await client.create_session(
                prompt=prompt, idempotency_key=task_id
            )
            session_id = session.get("session_id", "")
            db.update_task_status(
                task_id, TaskStatus.IN_PROGRESS, devin_job_id=session_id
            )
            db.add_log(
                task_id=task_id,
                level="INFO",
                message=f"Devin session started: {session_id}",
            )

            result = await client.poll_until_complete(session_id)
            devin_status = result.get("status_enum", result.get("status", "failed"))
            our_status = client.map_devin_status(devin_status)

            result_text = result.get("structured_output", str(result))
            if our_status == TaskStatus.COMPLETED:
                db.update_task_status(
                    task_id, TaskStatus.COMPLETED, result=str(result_text)
                )
                db.add_log(
                    task_id=task_id, level="INFO", message="Task completed successfully"
                )
            else:
                db.update_task_status(
                    task_id,
                    our_status,
                    error=f"Devin session ended with status: {devin_status}",
                )
                db.add_log(
                    task_id=task_id,
                    level="WARNING",
                    message=f"Devin session ended: {devin_status}",
                )

            return {"status": our_status.value, "result": result_text}

        except Exception as exc:
            logger.exception("Execution failed for task %s", task_id)
            db.update_task_status(task_id, TaskStatus.FAILED, error=str(exc))
            db.add_log(
                task_id=task_id,
                level="ERROR",
                message=f"Execution error: {exc}",
            )
            return {"status": TaskStatus.FAILED.value, "error": str(exc)}
