from abc import ABC, abstractmethod
from typing import Callable, Any, Awaitable

from interface.enum_type import EventType


AsyncHandler = Callable[[Any], Awaitable[None]]


class EventBus(ABC):
    """defines the publishing/subscribe interface for async event routing."""

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        """register handler to be called whenever event_type is published."""

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        """remove handler from the subscribers of event_type."""

    @abstractmethod
    async def publish(self, event_type: EventType, data: Any) -> None:
        """dispatch data to every handler subscribed to event_type."""
