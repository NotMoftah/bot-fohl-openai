
from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.dto import TelegramMessageDTO
from handler.incoming_telegram_messages_handler import IncomingTelegramMessagesHandler
from interface.event_type import EventType


@pytest.fixture()
def mock_bus() -> MagicMock:
    """Provide a mock EventBus with an async publish method."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture()
def handler(mock_bus: MagicMock) -> IncomingTelegramMessagesHandler:
    h = IncomingTelegramMessagesHandler()
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
    )


class TestIncomingTelegramMessagesHandlerInit:
    def test_init_returns_true_on_success(self, mock_bus: MagicMock) -> None:
        # Arrange
        h = IncomingTelegramMessagesHandler()

        # Act
        result = h.init(mock_bus)

        # Assert
        assert result is True

    def test_init_subscribes_to_incoming_telegram_message_event(
        self, mock_bus: MagicMock
    ) -> None:
        # Arrange
        h = IncomingTelegramMessagesHandler()

        # Act
        h.init(mock_bus)

        # Assert
        mock_bus.subscribe.assert_called_once_with(
            EventType.INCOMING_TELEGRAM_MESSAGE,
            h.handle_incoming_telegram_message,
        )


class TestIncomingTelegramMessagesHandlerHandle:
    async def test_handle_incoming_telegram_message_publishes_send_event(
        self, handler: IncomingTelegramMessagesHandler, mock_bus: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # Arrange / Act
        await handler.handle_incoming_telegram_message(incoming_message)

        # Assert
        mock_bus.publish.assert_awaited_once()
        event_type, reply = mock_bus.publish.call_args.args
        assert event_type == EventType.SEND_TELEGRAM_MESSAGE

    async def test_handle_incoming_telegram_message_reply_contains_original_text(
        self, handler: IncomingTelegramMessagesHandler, mock_bus: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # Arrange / Act
        await handler.handle_incoming_telegram_message(incoming_message)

        # Assert
        _, reply = mock_bus.publish.call_args.args
        assert "hi there" in reply.text

    async def test_handle_incoming_telegram_message_reply_preserves_chat_id(
        self, handler: IncomingTelegramMessagesHandler, mock_bus: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # Arrange / Act
        await handler.handle_incoming_telegram_message(incoming_message)

        # Assert
        _, reply = mock_bus.publish.call_args.args
        assert reply.chat_id == incoming_message.chat_id

    async def test_handle_incoming_telegram_message_reply_has_none_message_id(
        self, handler: IncomingTelegramMessagesHandler, mock_bus: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # Arrange / Act
        await handler.handle_incoming_telegram_message(incoming_message)

        # Assert — outgoing replies have no message_id yet
        _, reply = mock_bus.publish.call_args.args
        assert reply.message_id is None

    async def test_handle_incoming_telegram_message_reply_preserves_chat_type(
        self, handler: IncomingTelegramMessagesHandler, mock_bus: MagicMock,
        incoming_message: TelegramMessageDTO,
    ) -> None:
        # Arrange / Act
        await handler.handle_incoming_telegram_message(incoming_message)

        # Assert
        _, reply = mock_bus.publish.call_args.args
        assert reply.chat_type == incoming_message.chat_type

