import logging

from telegram import Bot

from entity.dto import TelegramMessageDTO
from interface import EventType, EventHandler, EventBus


class SendTelegramMessagesHandler(EventHandler):
    def __init__(self, token):
        self._bus = None
        self._bot = None
        self._token = token
        self._logger = logging.getLogger(self.__class__.__name__)

    def init(self, bus):
        self._bus = bus
        self._bot = Bot(token=self._token)

        bus.subscribe(EventType.send_telegram_message, self.handle_sending_telegram_message)
        return True

    async def handle_sending_telegram_message(self, message: TelegramMessageDTO):
        self._logger.info(f"sending telegram message: {message}")
        # initialize telegram bot if not already initialized and send the message back
        if not self._bot.application:
            await self._bot.initialize()
        await self._bot.send_message(chat_id=message.chat_id, text=message.text)