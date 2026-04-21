"""Client for the Devin AI API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import httpx

from app.core.config import TaskStatus, get_settings

logger = logging.getLogger(__name__)


class DevinClient:
    """Async wrapper around the Devin REST API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_url = settings.devin_api_url.rstrip("/")
        self.api_key = settings.devin_api_key
        self.org_id = settings.devin_org_id
        self.poll_interval = settings.devin_poll_interval

    @property
    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.org_id:
            headers["X-Devin-Org-Id"] = self.org_id
        return headers

    async def create_session(
        self,
        prompt: str,
        *,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new Devin session and return the response payload."""
        payload: dict[str, Any] = {"prompt": prompt}
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.api_url}/sessions",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            logger.info("Devin session created: %s", data.get("session_id"))
            return data

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve the current state of a Devin session."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_url}/sessions/{session_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def send_message(self, session_id: str, message: str) -> dict[str, Any]:
        """Send a follow-up message to an existing Devin session."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.api_url}/sessions/{session_id}/messages",
                headers=self._headers,
                json={"message": message},
            )
            resp.raise_for_status()
            return resp.json()

    async def poll_until_complete(
        self,
        session_id: str,
        *,
        timeout: int = 3600,
    ) -> dict[str, Any]:
        """Poll a session until it reaches a terminal state or *timeout* seconds elapse."""
        terminal_statuses = {"finished", "stopped", "failed"}
        elapsed = 0
        while elapsed < timeout:
            data = await self.get_session(session_id)
            status = data.get("status_enum", data.get("status", ""))
            logger.debug("Devin session %s status: %s", session_id, status)
            if status in terminal_statuses:
                return data
            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise TimeoutError(
            f"Devin session {session_id} did not complete within {timeout}s"
        )

    @staticmethod
    def map_devin_status(devin_status: str) -> TaskStatus:
        """Map a Devin session status string to our internal TaskStatus."""
        mapping: dict[str, TaskStatus] = {
            "running": TaskStatus.IN_PROGRESS,
            "blocked": TaskStatus.IN_PROGRESS,
            "finished": TaskStatus.COMPLETED,
            "stopped": TaskStatus.CANCELLED,
            "failed": TaskStatus.FAILED,
        }
        return mapping.get(devin_status, TaskStatus.IN_PROGRESS)


_client: Optional[DevinClient] = None


def get_devin_client() -> DevinClient:
    global _client
    if _client is None:
        _client = DevinClient()
    return _client
