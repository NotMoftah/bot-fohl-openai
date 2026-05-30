import datetime
import logging

import pytest

from unittest.mock import AsyncMock, MagicMock, call, patch

from entity.dto import ChatType, TelegramMessageDTO, UserCommandDTO
from entity.models import ChatMessage
from handler.incoming_user_command_handler import IncomingUserCommandHandler
from interface.enum_type import EventType, UserCommandType


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_chat_message(text: str, chat_id: int = 999, timestamp: int = 1_780_000_000) -> ChatMessage:
    return ChatMessage(
        message_id=None,
        chat_id=chat_id,
        username="bot",
        text=text,
        chat_type=ChatType.PRIVATE,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_repo() -> MagicMock:
    """provide a mock IBotMessageRepository."""
    repo = MagicMock()
    repo.get_by_chat_id_in_range = MagicMock(return_value=[])
    return repo


@pytest.fixture()
def mock_bus() -> MagicMock:
    """provide a mock EventBus with an async publish method."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture()
def handler(mock_bus: MagicMock, mock_repo: MagicMock) -> IncomingUserCommandHandler:
    h = IncomingUserCommandHandler(bot_messages_repo=mock_repo)
    h.init(mock_bus)
    return h


@pytest.fixture()
def list_actions_command() -> UserCommandDTO:
    return UserCommandDTO(
        type=UserCommandType.LIST_ACTIONS,
        chat_id=999,
        username="alice",
    )


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

class TestIncomingUserCommandHandlerInit:
    def test_init_returns_true_on_success(
        self, mock_bus: MagicMock, mock_repo: MagicMock
    ) -> None:
        # arrange
        h = IncomingUserCommandHandler(bot_messages_repo=mock_repo)

        # act
        result = h.init(mock_bus)

        # assert
        assert result is True

    def test_init_subscribes_to_incoming_user_command_event(
        self, mock_bus: MagicMock, mock_repo: MagicMock
    ) -> None:
        # arrange
        h = IncomingUserCommandHandler(bot_messages_repo=mock_repo)

        # act
        h.init(mock_bus)

        # assert
        mock_bus.subscribe.assert_called_once_with(
            EventType.INCOMING_USER_COMMAND,
            h.handle_incoming_user_command,
        )


# ---------------------------------------------------------------------------
# handle_incoming_user_command -- LIST_ACTIONS
# ---------------------------------------------------------------------------

class TestIncomingUserCommandHandlerHandleListActions:
    async def test_handle_calls_get_by_chat_id_in_range(
        self,
        handler: IncomingUserCommandHandler,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        mock_repo.get_by_chat_id_in_range.assert_called_once()

    async def test_handle_passes_correct_chat_id_to_repo(
        self,
        handler: IncomingUserCommandHandler,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        kwargs = mock_repo.get_by_chat_id_in_range.call_args.kwargs
        assert kwargs["chat_id"] == list_actions_command.chat_id

    async def test_handle_does_not_publish_when_no_actions_returned(
        self,
        handler: IncomingUserCommandHandler,
        mock_bus: MagicMock,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange
        mock_repo.get_by_chat_id_in_range.return_value = []

        # act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        mock_bus.publish.assert_not_called()

    async def test_handle_publishes_send_telegram_message_for_each_action(
        self,
        handler: IncomingUserCommandHandler,
        mock_bus: MagicMock,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange
        mock_repo.get_by_chat_id_in_range.return_value = [
            _make_chat_message("action one"),
            _make_chat_message("action two"),
        ]

        # act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        assert mock_bus.publish.call_count == 2
        for published_call in mock_bus.publish.call_args_list:
            assert published_call.args[0] == EventType.SEND_TELEGRAM_MESSAGE

    async def test_handle_publishes_correct_text_per_action(
        self,
        handler: IncomingUserCommandHandler,
        mock_bus: MagicMock,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange
        mock_repo.get_by_chat_id_in_range.return_value = [
            _make_chat_message("go for a run"),
        ]

        # act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        published_dto: TelegramMessageDTO = mock_bus.publish.call_args.args[1]
        assert published_dto.text == "go for a run"

    async def test_handle_publishes_dto_with_correct_chat_id(
        self,
        handler: IncomingUserCommandHandler,
        mock_bus: MagicMock,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange
        mock_repo.get_by_chat_id_in_range.return_value = [
            _make_chat_message("some action"),
        ]

        # act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        published_dto: TelegramMessageDTO = mock_bus.publish.call_args.args[1]
        assert published_dto.chat_id == list_actions_command.chat_id

    async def test_handle_publishes_dto_with_bot_username(
        self,
        handler: IncomingUserCommandHandler,
        mock_bus: MagicMock,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
    ) -> None:
        # arrange
        mock_repo.get_by_chat_id_in_range.return_value = [
            _make_chat_message("some action"),
        ]

        # act
        await handler.handle_incoming_user_command(list_actions_command)

        # assert
        published_dto: TelegramMessageDTO = mock_bus.publish.call_args.args[1]
        assert published_dto.username == "bot"

    async def test_handle_list_today_actions_also_triggers_publish(
        self,
        handler: IncomingUserCommandHandler,
        mock_bus: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        # arrange
        mock_repo.get_by_chat_id_in_range.return_value = [
            _make_chat_message("morning run"),
        ]
        command = UserCommandDTO(
            type=UserCommandType.LIST_TODAY_ACTIONS,
            chat_id=999,
            username="alice",
        )

        # act
        await handler.handle_incoming_user_command(command)

        # assert
        mock_bus.publish.assert_called_once()
        published_dto: TelegramMessageDTO = mock_bus.publish.call_args.args[1]
        assert published_dto.text == "morning run"

    async def test_handle_logs_received_command(
        self,
        handler: IncomingUserCommandHandler,
        mock_repo: MagicMock,
        list_actions_command: UserCommandDTO,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # arrange / act
        with caplog.at_level(logging.INFO, logger="IncomingUserCommandHandler"):
            await handler.handle_incoming_user_command(list_actions_command)

        # assert
        messages = [r.message for r in caplog.records]
        assert any("received" in m for m in messages)


# ---------------------------------------------------------------------------
# _get_action_timestamp_range
# ---------------------------------------------------------------------------

class TestGetActionTimestampRange:
    def test_get_action_timestamp_range_low_is_start_of_today(self) -> None:
        # arrange
        real_datetime = datetime.datetime
        fixed_now = real_datetime(2026, 5, 30, 14, 0, 0)

        # act
        with patch("handler.incoming_user_command_handler.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *a, **kw: real_datetime(*a, **kw)
            low, _ = IncomingUserCommandHandler._get_action_timestamp_range(days_ahead=7)

        # assert
        expected_low = int(real_datetime(2026, 5, 30, 0, 0, 0).timestamp())
        assert low == expected_low

    def test_get_action_timestamp_range_high_is_days_ahead_from_start_of_today(self) -> None:
        # arrange
        real_datetime = datetime.datetime
        fixed_now = real_datetime(2026, 5, 30, 14, 0, 0)

        # act
        with patch("handler.incoming_user_command_handler.datetime.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *a, **kw: real_datetime(*a, **kw)
            _, high = IncomingUserCommandHandler._get_action_timestamp_range(days_ahead=7)

        # assert
        expected_high = int(
            (real_datetime(2026, 5, 30, 0, 0, 0) + datetime.timedelta(days=7)).timestamp()
        )
        assert high == expected_high

    def test_get_action_timestamp_range_low_is_less_than_high(self) -> None:
        # arrange / act
        low, high = IncomingUserCommandHandler._get_action_timestamp_range(days_ahead=7)

        # assert
        assert low < high

