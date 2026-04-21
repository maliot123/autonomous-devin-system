"""FastAPI Task API server."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agents.memory_agent import MemoryAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.result_agent import ResultAgent
from app.core.config import TaskPriority, TaskStatus, TaskType, get_settings
from app.database.db import get_db, init_db
from app.workers.worker import enqueue_task

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autonomous Engineering System API",
    description=(
        "Task API for the Autonomous Engineering System. "
        "Used by Telegram bot, Hermes, and other integrations."
    ),
    version="1.0.0",
)


# ── Pydantic schemas ────────────────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    task_type: TaskType
    description: str
    repository: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    task_type: Optional[str] = None
    description: Optional[str] = None
    repository: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    devin_job_id: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SystemStatusResponse(BaseModel):
    status: str
    total_tasks: int
    status_breakdown: dict[str, int]
    agents: list[dict[str, Any]]


class LogEntry(BaseModel):
    log_id: str
    task_id: Optional[str] = None
    level: str
    message: str
    details: Optional[str] = None
    created_at: Optional[str] = None


# ── Lifecycle events ────────────────────────────────────────────────────

@app.on_event("startup")
async def startup() -> None:
    init_db()
    logger.info("API server started")


# ── Endpoints ───────────────────────────────────────────────────────────

@app.post("/task/create", response_model=TaskCreateResponse)
async def create_task(req: TaskCreateRequest) -> TaskCreateResponse:
    """Create a new engineering task (used by Telegram and Hermes)."""
    planner = PlannerAgent()
    plan = planner.plan(req.description, req.repository)

    db = get_db()
    task = db.create_task(
        task_type=req.task_type,
        description=req.description,
        repository=req.repository,
        priority=req.priority,
    )
    db.add_log(
        task_id=task.task_id,
        level="INFO",
        message=f"Task created: {req.task_type.value}",
        details=str(plan),
    )

    enqueue_task(task.task_id)

    return TaskCreateResponse(
        task_id=task.task_id,
        status="queued",
        message=f"Task queued for execution via {plan['task_type']}",
    )


@app.get("/task/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get current status of a task."""
    db = get_db()
    task = db.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    d = task.to_dict()
    return TaskStatusResponse(**d)


@app.get("/task/result/{task_id}")
async def get_task_result(task_id: str) -> dict[str, Any]:
    """Get the result of a completed task."""
    agent = ResultAgent()
    result = agent.format_api_response(task_id)
    if "error" in result and result["error"] == "Task not found":
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@app.get("/system/status", response_model=SystemStatusResponse)
async def system_status() -> SystemStatusResponse:
    """Get overall system health and statistics."""
    memory = MemoryAgent()
    summary = memory.get_system_summary()
    return SystemStatusResponse(
        status="operational",
        total_tasks=summary["total_tasks"],
        status_breakdown=summary["status_breakdown"],
        agents=summary["agents"],
    )


@app.get("/logs", response_model=list[LogEntry])
async def get_logs(task_id: Optional[str] = None, limit: int = 100) -> list[LogEntry]:
    """Retrieve execution logs, optionally filtered by task_id."""
    db = get_db()
    logs = db.get_logs(task_id=task_id, limit=limit)
    return [LogEntry(**lg.to_dict()) for lg in logs]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
