from abc import ABC, abstractmethod

from event_bus import EventBus


class EventHandler(ABC):
    @abstractmethod
    def init(self, bus: EventBus) -> bool:
        """All payment processors must implement this to charge money."""
        pass