import asyncio
import logging

from typing import Any, Dict, Set

from interface.event_bus import AsyncHandler, EventBus


class AsyncEventBus(EventBus):
    _instance: EventBus | None = None

    def __new__(cls) -> EventBus:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._logger = logging.getLogger(self.__class__.__name__)
        self._subscribers: Dict[str, Set[AsyncHandler]] = {}

    def subscribe(self, event_type: str, handler: AsyncHandler) -> None:
        """Register an async callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(handler)

    def unsubscribe(self, event_type: str, handler: AsyncHandler) -> None:
        """Remove a callback from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(handler)

    async def publish(self, event_type: str, data: Any) -> None:
        """
        Publish data to all subscribers of an event type asynchronously.
        Fires all handlers concurrently for maximum speed.
        """
        handlers = self._subscribers.get(event_type)
        if not handlers:
            return

        # Python 3.11+ TaskGroup runs all handlers concurrently.
        # _safe_execute absorbs individual failures so no task cancels its siblings.
        async with asyncio.TaskGroup() as tg:
            for handler in handlers:
                tg.create_task(self._safe_execute(handler, data))

    async def _safe_execute(self, handler: AsyncHandler, data: Any) -> None:
        """Ensure one failing subscriber does not crash the entire bus."""
        try:
            await handler(data)
        except Exception as e:
            # Log and swallow — do NOT re-raise so TaskGroup keeps running
            # all remaining sibling tasks instead of cancelling them.
            self._logger.error(
                f"Handler '{handler.__name__}' raised an error: {e}", exc_info=True
            )


# singleton
async_event_bus: EventBus = AsyncEventBus()

