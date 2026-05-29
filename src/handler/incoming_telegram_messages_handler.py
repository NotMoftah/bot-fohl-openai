import logging

from entity.dto import TelegramMessageDTO
from interface.event_bus import EventBus
from interface.event_handler import EventHandler
from interface.event_type import EventType


class IncomingTelegramMessagesHandler(EventHandler):
    """subscribes to incoming messages and re-publishes an echo reply."""

    def __init__(self) -> None:
        self._event_bus: EventBus | None = None
        self._logger = logging.getLogger(self.__class__.__name__)

    def init(self, event_bus: EventBus) -> bool:
        """subscribe to EventType.INCOMING_TELEGRAM_MESSAGE on event_bus."""
        self._event_bus = event_bus
        event_bus.subscribe(
            EventType.INCOMING_TELEGRAM_MESSAGE,
            self.handle_incoming_telegram_message,
        )
        return True

    async def handle_incoming_telegram_message(self, message: TelegramMessageDTO) -> None:
        """echo the original message text back to the sender via the bus."""
        self._logger.info(f"received incoming telegram message: {message}")

        # dispatch reply back through the bus so the send handler can deliver it
        reply = TelegramMessageDTO(
            message_id=None,
            chat_id=message.chat_id,
            text=f"got: {message.text}",
            chat_type=message.chat_type,
            username=message.username,
        )
        await self._event_bus.publish(EventType.SEND_TELEGRAM_MESSAGE, reply)
