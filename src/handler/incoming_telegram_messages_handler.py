import logging

from entity.dto import TelegramMessageDTO
from interface.event_bus import EventBus
from interface.event_handler import EventHandler
from interface.event_type import EventType


class IncomingTelegramMessagesHandler(EventHandler):
    def __init__(self):
        self._event_bus = None
        self._logger = logging.getLogger(self.__class__.__name__)

    def init(self, event_bus: EventBus):
        self._event_bus = event_bus

        event_bus.subscribe(EventType.incoming_telegram_message, self.handle_incoming_telegram_message)
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
        await self._event_bus.publish(EventType.send_telegram_message, replay)
