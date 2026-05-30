import logging

from entity.dto import TelegramMessageDTO
from entity.models import ChatMessage
from interface.dynamodb_repository import IChatMessageRepository
from interface.event_bus import EventBus
from interface.event_handler import EventHandler
from interface.event_type import EventType


class IncomingTelegramMessagesHandler(EventHandler):
    """subscribes to incoming messages and re-publishes an echo reply."""

    def __init__(self, messages_repo: IChatMessageRepository) -> None:
        self._event_bus: EventBus | None = None
        self._logger = logging.getLogger(self.__class__.__name__)
        self._messages_repo: IChatMessageRepository | None = messages_repo

    def init(self, event_bus: EventBus) -> bool:
        """subscribe to EventType.INCOMING_TELEGRAM_MESSAGE on event_bus."""
        self._event_bus = event_bus
        event_bus.subscribe(
            EventType.INCOMING_TELEGRAM_MESSAGE,
            self.handle_incoming_telegram_message,
        )
        return True

    async def handle_incoming_telegram_message(self, message: TelegramMessageDTO) -> None:
        """store incoming telegram messages into message repository."""
        self._logger.info(f"received incoming telegram message: {message.message_id}")
        self._messages_repo.save(ChatMessage(
            message_id=message.message_id,
            chat_id=message.chat_id,
            text=message.text,
            chat_type=message.chat_type,
            username=message.username,
            timestamp=message.timestamp,
            raw_payload=message.raw_payload,
        ))
        self._logger.info(f"saved message to repository: {message.message_id}")