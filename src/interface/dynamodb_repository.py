from abc import ABC, abstractmethod

from entity.models import ChatMessage


class IUserMessageRepository(ABC):
    @abstractmethod
    def get_by_chat_id(self, chat_id: int) -> list[ChatMessage]:
        """get all chat messages for a given chat_id."""
        pass

    @abstractmethod
    def get_by_chat_id_in_range(
        self, chat_id: int, timestamp_low: int, timestamp_high: int
    ) -> list[ChatMessage]:
        """get all chat messages for a given chat_id within a specific timestamp range."""
        pass

    @abstractmethod
    def save(self, chat_message: ChatMessage) -> bool:
        """save a chat message to dynamodb."""
        pass


class IBotMessageRepository(ABC):
    @abstractmethod
    def get_by_chat_id(self, chat_id: int) -> list[ChatMessage]:
        """get all bot messages for a given chat_id."""""
        pass

    @abstractmethod
    def get_by_chat_id_in_range(
        self, chat_id: int, timestamp_low: int, timestamp_high: int
    ) -> list[ChatMessage]:
        """get all bot messages for a given chat_id within a specific timestamp range."""
        pass

    @abstractmethod
    def save(self, chat_message: ChatMessage) -> bool:
        """save a bot message to dynamodb."""
        pass