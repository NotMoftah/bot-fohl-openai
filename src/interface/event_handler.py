from abc import ABC, abstractmethod

from .event_bus import EventBus


class EventHandler(ABC):
    """Encapsulates the subscription lifecycle for a single concern."""

    @abstractmethod
    def init(self, bus: EventBus) -> bool:
        """Subscribe to the relevant event type(s) on *bus* and return True on success."""
