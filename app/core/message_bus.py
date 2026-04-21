"""Simple in-process message bus for decoupled component communication."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

Callback = Callable[..., Coroutine[Any, Any, None]]


class MessageBus:
    """Publish / subscribe message bus.

    Components publish events (e.g. ``task.created``, ``task.completed``) and
    other components subscribe to react.  All handlers run as fire-and-forget
    ``asyncio`` tasks so publishers are never blocked.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callback]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callback) -> None:
        self._subscribers[event].append(callback)
        logger.debug("Subscribed %s to event '%s'", callback.__name__, event)

    def unsubscribe(self, event: str, callback: Callback) -> None:
        try:
            self._subscribers[event].remove(callback)
        except ValueError:
            pass

    async def publish(self, event: str, **kwargs: Any) -> None:
        handlers = self._subscribers.get(event, [])
        logger.debug("Publishing event '%s' to %d handler(s)", event, len(handlers))
        for handler in handlers:
            asyncio.create_task(self._safe_call(handler, event, **kwargs))

    @staticmethod
    async def _safe_call(handler: Callback, event: str, **kwargs: Any) -> None:
        try:
            await handler(**kwargs)
        except Exception:
            logger.exception(
                "Error in handler %s for event '%s'", handler.__name__, event
            )


# Global singleton
message_bus = MessageBus()
