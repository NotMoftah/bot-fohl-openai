from abc import ABC, abstractmethod
from typing import Callable, Any, Awaitable

from .event_type import EventType

AsyncHandler = Callable[[Any], Awaitable[None]]


class EventBus(ABC):
    @abstractmethod
    def subscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: AsyncHandler) -> None:
        pass

    @abstractmethod
    async def publish(self, event_type: EventType, data: Any) -> None:
        pass
