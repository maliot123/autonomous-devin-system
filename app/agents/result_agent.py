"""Result agent — formats and delivers task results."""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.database.db import get_db

logger = logging.getLogger(__name__)


class ResultAgent:
    """Retrieve and format the output of completed tasks."""

    def get_result(self, task_id: str) -> Optional[dict[str, Any]]:
        db = get_db()
        task = db.get_task(task_id)
        if task is None:
            return None
        return {
            "task_id": task.task_id,
            "status": task.status.value if task.status else None,
            "result": task.result,
            "error": task.error,
        }

    def format_telegram_message(self, task_id: str) -> str:
        data = self.get_result(task_id)
        if data is None:
            return f"Task {task_id} not found."

        status = data.get("status", "unknown")
        lines = [
            f"Task: {task_id}",
            f"Status: {status}",
        ]
        if data.get("result"):
            result_preview = str(data["result"])[:500]
            lines.append(f"Result:\n{result_preview}")
        if data.get("error"):
            lines.append(f"Error: {data['error']}")
        return "\n".join(lines)

    def format_api_response(self, task_id: str) -> dict[str, Any]:
        data = self.get_result(task_id)
        if data is None:
            return {"error": "Task not found", "task_id": task_id}
        return data
