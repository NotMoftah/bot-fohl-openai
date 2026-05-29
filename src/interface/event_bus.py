from abc import ABC, abstractmethod
from typing import Callable, Any, Awaitable

from .event_type import EventType


AsyncHandler = Callable[[Any], Awaitable[None]]


class EventBus(ABC):
    """Defines the publishing/subscribe interface for async event routing."""

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        """Register *handler* to be called whenever *event_type* is published."""

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        """Remove *handler* from the subscribers of *event_type*."""

    @abstractmethod
    async def publish(self, event_type: EventType, data: Any) -> None:
        """Dispatch *data* to every handler subscribed to *event_type*."""
