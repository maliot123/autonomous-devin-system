"""Telegram bot — command console for the Autonomous Engineering System."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.core.config import TaskPriority, TaskType, get_settings

logger = logging.getLogger(__name__)


def _api_base() -> str:
    s = get_settings()
    return f"http://{s.api_host}:{s.api_port}"


async def _post_task(
    task_type: TaskType,
    description: str,
    repository: str | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "task_type": task_type.value,
        "description": description,
        "priority": priority.value,
    }
    if repository:
        payload["repository"] = repository
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_api_base()}/task/create", json=payload)
        resp.raise_for_status()
        return resp.json()


# ── Command handlers ────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Autonomous Engineering System\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/status - System status\n"
        "/agents - List agents\n"
        "/build <description> - Generate code\n"
        "/task <description> - Create generic task\n"
        "/repo <url> - Analyze repository\n"
        "/deploy <description> - Setup deployment\n"
        "/logs [task_id] - View logs\n"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{_api_base()}/system/status")
            resp.raise_for_status()
            data = resp.json()
        text = (
            f"System Status: {data['status']}\n"
            f"Total Tasks: {data['total_tasks']}\n"
            f"Breakdown: {data['status_breakdown']}"
        )
    except Exception as exc:
        text = f"Failed to fetch status: {exc}"
    await update.message.reply_text(text)


async def cmd_agents(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{_api_base()}/system/status")
            resp.raise_for_status()
            data = resp.json()
        agents = data.get("agents", [])
        if not agents:
            text = "No agents registered."
        else:
            lines = [f"- {a['name']} ({a['agent_type']}): {a['status']}" for a in agents]
            text = "Agents:\n" + "\n".join(lines)
    except Exception as exc:
        text = f"Failed to fetch agents: {exc}"
    await update.message.reply_text(text)


async def cmd_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    description = " ".join(context.args) if context.args else ""
    if not description:
        await update.message.reply_text("Usage: /build <description>")
        return
    try:
        result = await _post_task(TaskType.CODE_GENERATION, description)
        await update.message.reply_text(
            f"Task created: {result['task_id']}\nStatus: {result['status']}"
        )
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    description = " ".join(context.args) if context.args else ""
    if not description:
        await update.message.reply_text("Usage: /task <description>")
        return
    try:
        result = await _post_task(TaskType.CODE_GENERATION, description)
        await update.message.reply_text(
            f"Task created: {result['task_id']}\nStatus: {result['status']}"
        )
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def cmd_repo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = context.args[0] if context.args else ""
    if not url:
        await update.message.reply_text("Usage: /repo <github_url>")
        return
    description = f"Analyze repository: {url}"
    try:
        result = await _post_task(
            TaskType.REPO_ANALYSIS, description, repository=url
        )
        await update.message.reply_text(
            f"Analysis task created: {result['task_id']}\nStatus: {result['status']}"
        )
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def cmd_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    description = " ".join(context.args) if context.args else ""
    if not description:
        await update.message.reply_text("Usage: /deploy <description>")
        return
    try:
        result = await _post_task(TaskType.DEPLOYMENT_SETUP, description)
        await update.message.reply_text(
            f"Deploy task created: {result['task_id']}\nStatus: {result['status']}"
        )
    except Exception as exc:
        await update.message.reply_text(f"Error: {exc}")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_id = context.args[0] if context.args else None
    try:
        params: dict[str, Any] = {"limit": 10}
        if task_id:
            params["task_id"] = task_id
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{_api_base()}/logs", params=params)
            resp.raise_for_status()
            logs = resp.json()
        if not logs:
            text = "No logs found."
        else:
            lines = [
                f"[{lg['level']}] {lg['message']}" for lg in logs[:10]
            ]
            text = "Recent logs:\n" + "\n".join(lines)
    except Exception as exc:
        text = f"Failed to fetch logs: {exc}"
    await update.message.reply_text(text)


def build_telegram_app() -> Application:
    """Construct the Telegram Application with all command handlers."""
    settings = get_settings()
    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("agents", cmd_agents))
    application.add_handler(CommandHandler("build", cmd_build))
    application.add_handler(CommandHandler("task", cmd_task))
    application.add_handler(CommandHandler("repo", cmd_repo))
    application.add_handler(CommandHandler("deploy", cmd_deploy))
    application.add_handler(CommandHandler("logs", cmd_logs))

    return application


def run_bot() -> None:
    """Start the Telegram bot (blocking)."""
    logger.info("Starting Telegram bot …")
    application = build_telegram_app()
    application.run_polling(drop_pending_updates=True)
