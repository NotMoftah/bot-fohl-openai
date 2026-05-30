import logging

from typing import Optional
from telegram import Bot

from entity.dto import ChatType, TelegramMessageDTO
from interface.event_bus import EventBus
from interface.event_handler import EventHandler
from interface.enum_type import EventType


class OutgoingTelegramMessageHandler(EventHandler):
    """subscribes to send-message events and forwards them to the telegram Bot API."""

    def __init__(self, token: Optional[str]) -> None:
        self._bus: EventBus | None = None
        self._token: Optional[str] = token
        self._logger = logging.getLogger(self.__class__.__name__)

    def init(self, bus: EventBus) -> bool:
        """subscribe to EventType.SEND_TELEGRAM_MESSAGE on bus."""
        self._bus = bus
        bus.subscribe(EventType.SEND_TELEGRAM_MESSAGE, self.handle_sending_telegram_message)
        return True

    async def handle_sending_telegram_message(self, message: TelegramMessageDTO) -> None:
        """send *message* to the telegram chat, skipping any non-private conversation."""
        if message.chat_type != ChatType.PRIVATE:
            # only respond in direct chats to avoid spamming groups
            self._logger.warning(
                f"skipping send for chat_type={message.chat_type!r} - only private chats are supported",
            )
            return

        if not self._token:
            raise RuntimeError("BOT_TOKEN is not configured; cannot send message")

        self._logger.info(f"sending telegram message: {message}")

        async with Bot(token=self._token) as bot:
            await bot.send_message(chat_id=message.chat_id, text=message.text)
