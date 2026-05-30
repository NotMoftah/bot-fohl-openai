import datetime
import logging

from entity.dto import ChatType, TelegramMessageDTO, UserCommandDTO
from interface.dynamodb_repository import IBotMessageRepository
from interface.event_bus import EventBus
from interface.event_handler import EventHandler
from interface.enum_type import EventType, UserCommandType


class IncomingUserCommandHandler(EventHandler):
    """subscribes to incoming messages and re-publishes an echo reply."""

    def __init__(self, bot_messages_repo: IBotMessageRepository) -> None:
        self._event_bus: EventBus | None = None
        self._logger = logging.getLogger(self.__class__.__name__)
        self._messages_repo: IBotMessageRepository | None = bot_messages_repo

    def init(self, event_bus: EventBus) -> bool:
        """subscribe to EventType.INCOMING_TELEGRAM_MESSAGE on event_bus."""
        self._event_bus = event_bus
        event_bus.subscribe(
            EventType.INCOMING_USER_COMMAND,
            self.handle_incoming_user_command,
        )
        return True

    async def handle_incoming_user_command(self, command: UserCommandDTO) -> None:
        """handles incoming user command."""
        self._logger.info(f"received incoming user command: "
                          f"{command.type} from {command.username} in chat {command.chat_id}")

        if command.type in [UserCommandType.LIST_ACTIONS, UserCommandType.LIST_TODAY_ACTIONS]:
            self._logger.info(f"user {command.username} requested today's actions")
            timestamp_low, timestamp_high = self._get_action_timestamp_range(days_ahead=7)
            actions = self._messages_repo.get_by_chat_id_in_range(
                chat_id=command.chat_id,
                timestamp_low=timestamp_low,
                timestamp_high=timestamp_high
            )
            for action in actions:
                await self._event_bus.publish(
                    EventType.SEND_TELEGRAM_MESSAGE,
                    TelegramMessageDTO(
                        message_id=0,
                        chat_id=command.chat_id,
                        username="bot",
                        text=action.text,
                        chat_type=ChatType.PRIVATE,
                        timestamp=int(datetime.datetime.now().timestamp()),
                        raw_payload={},
                    )
                )

    @staticmethod
    def _get_action_timestamp_range(days_ahead: int) -> tuple[int, int]:
        """returns the timestamp range for today's actions."""
        now = datetime.datetime.now()
        start_of_day = datetime.datetime(now.year, now.month, now.day)
        end_of_day_plus_days_ahead = start_of_day + datetime.timedelta(days=days_ahead)
        return int(start_of_day.timestamp()), int(end_of_day_plus_days_ahead.timestamp())