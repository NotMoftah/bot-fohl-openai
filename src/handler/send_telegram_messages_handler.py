import logging

from telegram import Bot

from entity.dto import TelegramMessageDTO
from interface.event_handler import EventHandler
from interface.event_type import EventType


class SendTelegramMessagesHandler(EventHandler):
    def __init__(self, token):
        self._bus = None
        self._token = token
        self._logger = logging.getLogger(self.__class__.__name__)

    def init(self, bus):
        self._bus = bus

        bus.subscribe(EventType.send_telegram_message, self.handle_sending_telegram_message)
        return True

    async def handle_sending_telegram_message(self, message: TelegramMessageDTO):
        self._logger.info(f"sending telegram message: {message}")

        async with Bot(token=self._token) as bot:
            await bot.send_message(chat_id=message.chat_id, text=message.text)
