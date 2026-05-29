from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entity.dto import ChatType, TelegramMessageDTO
from handler.send_telegram_messages_handler import SendTelegramMessagesHandler
from interface.event_type import EventType


@pytest.fixture()
def mock_bus() -> MagicMock:
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture()
def handler(mock_bus: MagicMock) -> SendTelegramMessagesHandler:
    h = SendTelegramMessagesHandler(token="fake_token")
    h.init(mock_bus)
    return h


def _make_message(chat_type: str = ChatType.PRIVATE) -> TelegramMessageDTO:
    return TelegramMessageDTO(
        message_id=None,
        chat_id=777,
        username="bob",
        text="hello",
        chat_type=chat_type,
    )


class TestSendTelegramMessagesHandlerInit:
    def test_init_returns_true_on_success(self, mock_bus: MagicMock) -> None:
        # Arrange
        h = SendTelegramMessagesHandler(token="tok")

        # Act
        result = h.init(mock_bus)

        # Assert
        assert result is True

    def test_init_subscribes_to_send_telegram_message_event(
        self, mock_bus: MagicMock
    ) -> None:
        # Arrange
        h = SendTelegramMessagesHandler(token="tok")

        # Act
        h.init(mock_bus)

        # Assert
        mock_bus.subscribe.assert_called_once_with(
            EventType.SEND_TELEGRAM_MESSAGE,
            h.handle_sending_telegram_message,
        )


class TestSendTelegramMessagesHandlerHandle:
    async def test_handle_sending_telegram_message_skips_non_private_chat(
        self, handler: SendTelegramMessagesHandler
    ) -> None:
        # arrange
        message = _make_message(chat_type=ChatType.GROUP)

        # act — must return without calling the Bot API
        with patch("handler.send_telegram_messages_handler.Bot") as mock_bot_cls:
            await handler.handle_sending_telegram_message(message)

        # assert
        mock_bot_cls.assert_not_called()

    async def test_handle_sending_telegram_message_logs_warning_for_non_private(
        self,
        handler: SendTelegramMessagesHandler,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # arrange
        import logging
        message = _make_message(chat_type=ChatType.SUPERGROUP)

        # act
        with patch("handler.send_telegram_messages_handler.Bot"):
            with caplog.at_level(logging.WARNING, logger="SendTelegramMessagesHandler"):
                await handler.handle_sending_telegram_message(message)

        # assert
        assert any("supergroup" in r.message for r in caplog.records)

    async def test_handle_sending_telegram_message_sends_message_for_private_chat(
        self, handler: SendTelegramMessagesHandler
    ) -> None:
        # arrange
        message = _make_message(chat_type=ChatType.PRIVATE)
        mock_bot = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)

        # Act
        with patch("handler.send_telegram_messages_handler.Bot", return_value=mock_bot):
            await handler.handle_sending_telegram_message(message)

        # Assert
        mock_bot.send_message.assert_awaited_once_with(
            chat_id=777, text="hello"
        )

    async def test_handle_sending_telegram_message_raises_when_token_is_missing(
        self, mock_bus: MagicMock
    ) -> None:
        # Arrange — handler initialised with no token
        h = SendTelegramMessagesHandler(token=None)
        h.init(mock_bus)
        message = _make_message(chat_type="private")

        # Act / Assert
        with pytest.raises(RuntimeError, match="BOT_TOKEN is not configured"):
            await h.handle_sending_telegram_message(message)

