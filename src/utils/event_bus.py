import asyncio
import logging

from typing import Any, Dict, Set

from interface.event_bus import AsyncHandler, EventBus
from interface.event_type import EventType


class AsyncEventBus(EventBus):
    """Thread-safe singleton event bus that fans out events to async subscribers.

    Uses :class:`asyncio.TaskGroup` (Python 3.11+) so all handlers run
    concurrently and a single failing handler never blocks its siblings.
    """

    _instance: "AsyncEventBus | None" = None

    def __new__(cls) -> "AsyncEventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized: bool = True
        self._logger = logging.getLogger(self.__class__.__name__)
        self._subscribers: Dict[str, Set[AsyncHandler]] = {}

    def subscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        """Register an async callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(handler)

    def unsubscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        """Remove a callback from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(handler)

    async def publish(self, event_type: EventType, data: Any) -> None:
        """Publish *data* to all subscribers of *event_type* concurrently."""
        handlers = self._subscribers.get(event_type)
        if not handlers:
            return

        # taskgroup runs all handlers concurrently; _safe_execute absorbs
        # individual failures so no task cancels its siblings.
        async with asyncio.TaskGroup() as tg:
            for handler in handlers:
                tg.create_task(self._safe_execute(handler, data))

    async def _safe_execute(self, handler: AsyncHandler, data: Any) -> None:
        """Invoke *handler* and absorb any exception it raises.

        Swallowing here is intentional — one bad subscriber must not prevent
        the remaining ones from receiving the event.
        """
        try:
            await handler(data)
        except Exception as exc:  # noqa: BLE001 — deliberate broad catch
            self._logger.error(
                "handler '%s' raised an unhandled error: %s",
                handler.__name__,
                exc,
                exc_info=True,
            )


# module-level singleton — initialised once at cold-start
async_event_bus: AsyncEventBus = AsyncEventBus()
