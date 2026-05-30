import logging

import pytest

from unittest.mock import AsyncMock, MagicMock

from entity.dto import TelegramMessageDTO, UserCommandDTO
from entity.models import ChatMessage
from handler.incoming_telegram_message_handler import IncomingTelegramMessageHandler
from interface.enum_type import EventType, UserCommandType


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_repo() -> MagicMock:
    """provide a mock IChatMessageRepository."""
    repo = MagicMock()
    repo.save = MagicMock(return_value=True)
    return repo


@pytest.fixture()
def mock_bus() -> MagicMock:
    """provide a mock EventBus with an async publish method."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture()
def handler(mock_bus: MagicMock, mock_repo: MagicMock) -> IncomingTelegramMessageHandler:
    h = IncomingTelegramMessageHandler(user_messages_repo=mock_repo)
    h.init(mock_bus)
    return h


@pytest.fixture()
def incoming_message() -> TelegramMessageDTO:
    return TelegramMessageDTO(
        message_id=1,
        chat_id=999,
        username="alice",
        text="hi there",
        chat_type="private",
        timestamp=1_780_000_000,
        raw_payload={"update_id": 42},
    )


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

class TestIncomingTelegramMessagesHandlerInit:
    def test_init_returns_true_on_success(self, mock_bus: MagicMock, mock_repo: MagicMock) -> None:
        # arrange
        h = IncomingTelegramMessageHandler(user_messages_repo=mock_repo)

        # act
        result = h.init(mock_bus)

        # assert
        assert result is True

    def test_init_subscribes_to_incoming_telegram_message_event(
        self, mock_bus: MagicMock, mock_repo: MagicMock
    ) -> None:
        # arrange
        h = IncomingTelegramMessageHandler(user_messages_repo=mock_repo)

        # act
        h.init(mock_bus)

        # assert
        mock_bus.subscribe.assert_called_once_with(
            EventType.INCOMING_USER_MESSAGE,
            h.handle_incoming_telegram_message,
        )


# ---------------------------------------------------------------------------
# handle_incoming_telegram_message
# ---------------------------------------------------------------------------

class TestIncomingTelegramMessagesHandlerHandle:
    async def test_handle_incoming_telegram_message_calls_repo_save(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        mock_repo.save.assert_called_once()

    async def test_handle_incoming_telegram_message_saves_chat_message_instance(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert isinstance(saved, ChatMessage)

    async def test_handle_incoming_telegram_message_maps_message_id(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.message_id == incoming_message.message_id

    async def test_handle_incoming_telegram_message_maps_chat_id(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.chat_id == incoming_message.chat_id

    async def test_handle_incoming_telegram_message_maps_text(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.text == incoming_message.text

    async def test_handle_incoming_telegram_message_maps_username(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.username == incoming_message.username

    async def test_handle_incoming_telegram_message_maps_chat_type(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.chat_type == incoming_message.chat_type

    async def test_handle_incoming_telegram_message_maps_timestamp(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.timestamp == incoming_message.timestamp

    async def test_handle_incoming_telegram_message_maps_raw_payload(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # arrange / act
        await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        saved: ChatMessage = mock_repo.save.call_args.args[0]
        assert saved.raw_payload == incoming_message.raw_payload

    async def test_handle_incoming_telegram_message_logs_received_and_saved(
        self,
        handler: IncomingTelegramMessageHandler,
        incoming_message: TelegramMessageDTO,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # arrange / act
        with caplog.at_level(logging.INFO, logger="IncomingTelegramMessageHandler"):
            await handler.handle_incoming_telegram_message(incoming_message)

        # assert
        messages = [r.message for r in caplog.records]
        assert any("received" in m for m in messages)
        assert any("saved" in m for m in messages)


# ---------------------------------------------------------------------------
# handle_incoming_telegram_message -- empty / None text guard
# ---------------------------------------------------------------------------

class TestIncomingTelegramMessageHandlerSkipsEmptyText:
    async def test_handle_skips_save_when_text_is_empty_string(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=2, chat_id=999, username="alice",
            text="", chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        mock_repo.save.assert_not_called()

    async def test_handle_skips_save_when_text_is_none(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=3, chat_id=999, username="alice",
            text=None, chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        mock_repo.save.assert_not_called()

    async def test_handle_does_not_publish_event_when_text_is_empty(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_bus: MagicMock,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=4, chat_id=999, username="alice",
            text="", chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        mock_bus.publish.assert_not_called()


# ---------------------------------------------------------------------------
# handle_incoming_telegram_message -- ellipsis triggers LIST_ACTIONS command
# ---------------------------------------------------------------------------

class TestIncomingTelegramMessageHandlerEllipsisCommand:
    @pytest.mark.parametrize("ellipsis_text", ["...", "\u2026"])
    async def test_handle_publishes_incoming_user_command_event(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_bus: MagicMock,
        ellipsis_text: str,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=5, chat_id=999, username="alice",
            text=ellipsis_text, chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        mock_bus.publish.assert_called_once()
        event_type = mock_bus.publish.call_args.kwargs["event_type"]
        assert event_type == EventType.INCOMING_USER_COMMAND

    @pytest.mark.parametrize("ellipsis_text", ["...", "\u2026"])
    async def test_handle_publishes_list_actions_command_type(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_bus: MagicMock,
        ellipsis_text: str,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=6, chat_id=999, username="alice",
            text=ellipsis_text, chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        data: UserCommandDTO = mock_bus.publish.call_args.kwargs["data"]
        assert data.type == UserCommandType.LIST_ACTIONS

    @pytest.mark.parametrize("ellipsis_text", ["...", "\u2026"])
    async def test_handle_publishes_command_with_correct_chat_id(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_bus: MagicMock,
        ellipsis_text: str,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=7, chat_id=999, username="alice",
            text=ellipsis_text, chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        data: UserCommandDTO = mock_bus.publish.call_args.kwargs["data"]
        assert data.chat_id == message.chat_id

    @pytest.mark.parametrize("ellipsis_text", ["...", "\u2026"])
    async def test_handle_publishes_command_with_correct_username(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_bus: MagicMock,
        ellipsis_text: str,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=8, chat_id=999, username="alice",
            text=ellipsis_text, chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        data: UserCommandDTO = mock_bus.publish.call_args.kwargs["data"]
        assert data.username == message.username

    @pytest.mark.parametrize("ellipsis_text", ["...", "\u2026"])
    async def test_handle_does_not_save_to_repo_when_ellipsis(
        self,
        handler: IncomingTelegramMessageHandler,
        mock_repo: MagicMock,
        ellipsis_text: str,
    ) -> None:
        # arrange
        message = TelegramMessageDTO(
            message_id=9, chat_id=999, username="alice",
            text=ellipsis_text, chat_type="private", timestamp=1_780_000_000,
        )

        # act
        await handler.handle_incoming_telegram_message(message)

        # assert
        mock_repo.save.assert_not_called()

