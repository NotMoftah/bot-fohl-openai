import logging

from entity.dto import TelegramMessageDTO
from interface import EventType, EventHandler, EventBus


class IncomingTelegramMessagesHandler(EventHandler):
    def __init__(self):
        self._bus = None
        self._logger = logging.getLogger(self.__class__.__name__)

    def init(self, bus):
        self._bus = bus

        bus.subscribe(EventType.incoming_telegram_message, self.handle_incoming_telegram_message)
        return True

    async def handle_incoming_telegram_message(self, message: TelegramMessageDTO):
        self._logger.info(f"received incoming telegram message: {message}")
        # send a replay to the user
        replay = TelegramMessageDTO(
            message_id=None,
            chat_id=message.chat_id,
            text=f"got: {message.text}",
            username=None
        )
        self._bus.publish(EventType.send_telegram_message, replay)
