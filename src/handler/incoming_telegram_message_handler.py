import logging

from entity.dto import TelegramMessageDTO, UserCommandDTO
from entity.models import ChatMessage
from interface.dynamodb_repository import IUserMessageRepository
from interface.event_bus import EventBus
from interface.event_handler import EventHandler
from interface.enum_type import EventType, UserCommandType


class IncomingTelegramMessageHandler(EventHandler):
    """subscribes to incoming messages and re-publishes an echo reply."""

    def __init__(self, user_messages_repo: IUserMessageRepository) -> None:
        self._event_bus: EventBus | None = None
        self._logger = logging.getLogger(self.__class__.__name__)
        self._messages_repo: IUserMessageRepository | None = user_messages_repo

    def init(self, event_bus: EventBus) -> bool:
        """subscribe to EventType.INCOMING_TELEGRAM_MESSAGE on event_bus."""
        self._event_bus = event_bus
        event_bus.subscribe(
            EventType.INCOMING_USER_MESSAGE,
            self.handle_incoming_telegram_message,
        )
        return True

    async def handle_incoming_telegram_message(self, message: TelegramMessageDTO) -> None:
        """store incoming telegram messages into message repository."""
        self._logger.info(f"received incoming telegram message: {message.message_id}")
        if message.text in ["", None]:
            self._logger.warning(f"skipping message with no text: {message.message_id}")
            return

        if message.text in ["...", "…"]:
            self._logger.info(f"user {message.username} requested today's actions")
            await self._event_bus.publish(
                event_type=EventType.INCOMING_USER_COMMAND,
                data=UserCommandDTO(
                    type=UserCommandType.LIST_ACTIONS,
                    chat_id=message.chat_id,
                    username=message.username
                )
            )
            return

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