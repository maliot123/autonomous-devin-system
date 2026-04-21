"""Centralized configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskType(str, Enum):
    CODE_GENERATION = "CODE_GENERATION"
    REPO_ANALYSIS = "REPO_ANALYSIS"
    BUG_FIX = "BUG_FIX"
    REFACTORING = "REFACTORING"
    AUTOMATION_SCRIPT = "AUTOMATION_SCRIPT"
    DEPLOYMENT_SETUP = "DEPLOYMENT_SETUP"
    AI_AGENT_CREATION = "AI_AGENT_CREATION"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Settings:
    # Telegram
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )

    # Devin
    devin_api_key: str = field(
        default_factory=lambda: os.getenv("DEVIN_API_KEY", "")
    )
    devin_org_id: str = field(
        default_factory=lambda: os.getenv("DEVIN_ORG_ID", "")
    )
    devin_api_url: str = field(
        default_factory=lambda: os.getenv(
            "DEVIN_API_URL", "https://api.devin.ai/v1"
        )
    )

    # GitHub
    github_token: str = field(
        default_factory=lambda: os.getenv("GITHUB_TOKEN", "")
    )

    # Redis
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    # Database
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "sqlite:///./data/autonomous_system.db"
        )
    )

    # API
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(
        default_factory=lambda: int(os.getenv("API_PORT", "8000"))
    )
    api_base_url: str = field(
        default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000")
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    log_file: str = field(
        default_factory=lambda: os.getenv("LOG_FILE", "logs/system.log")
    )

    # Polling
    devin_poll_interval: int = field(
        default_factory=lambda: int(os.getenv("DEVIN_POLL_INTERVAL", "30"))
    )

    def validate(self) -> list[str]:
        """Return a list of missing required settings."""
        missing: list[str] = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.devin_api_key:
            missing.append("DEVIN_API_KEY")
        return missing


def get_settings() -> Settings:
    """Return a fresh ``Settings`` instance (reads env vars at call time)."""
    return Settings()
