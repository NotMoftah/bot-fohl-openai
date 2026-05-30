import asyncio
import json
import logging

import pytest

from unittest.mock import AsyncMock, patch

from entity.dto import TelegramMessageDTO
from interface.enum_type import EventType
from lambda_function import lambda_handler


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_event(body: object) -> dict:
    """wrap body in a minimal api gateway proxy event dict."""
    return {"body": json.dumps(body)}


def _close_coro(coro: object) -> None:
    """close a coroutine immediately so gc does not emit ResourceWarnings."""
    if hasattr(coro, "close"):
        coro.close()  # type: ignore[union-attr]


def _run_coro(coro: object) -> None:
    """run a coroutine in a fresh event loop so we can inspect publish calls."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(coro)  # type: ignore[arg-type]
    finally:
        loop.close()


VALID_TELEGRAM_BODY: dict = {
    "update_id": 123,
    "message": {
        "message_id": 1,
        "text": "hello",
        "from": {"username": "alice"},
        "chat": {"id": 42, "type": "private"},
        "date": 1780000000,
    },
}


# ---------------------------------------------------------------------------
# response status codes
# ---------------------------------------------------------------------------

class TestLambdaHandlerResponse:
    def test_lambda_handler_valid_telegram_message_returns_200(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)

        # act
        with patch("lambda_function.asyncio.run", side_effect=_close_coro):
            result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 200
        assert result["body"] == "ok"

    def test_lambda_handler_invalid_json_body_returns_400(self) -> None:
        # arrange
        event = {"body": "not valid json {{{"}

        # act
        result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 400
        assert "Invalid JSON" in result["body"]

    def test_lambda_handler_empty_body_returns_200(self) -> None:
        # arrange - no body key at all
        event: dict = {}

        # act
        result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 200

    def test_lambda_handler_body_without_update_id_returns_200_without_publishing(
        self,
    ) -> None:
        # arrange
        event = _make_event({"some_other_key": "value"})

        # act
        with patch("lambda_function.asyncio.run") as mock_run:
            result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 200
        mock_run.assert_not_called()

    def test_lambda_handler_missing_message_field_in_telegram_body_returns_200(
        self,
    ) -> None:
        # arrange - update_id present but 'message' key missing, not a recognised update shape
        event = _make_event({"update_id": 1})

        # act
        result = lambda_handler(event, {})

        # assert - no message key means we skip publishing and return 200
        assert result["statusCode"] == 200

    def test_lambda_handler_missing_nested_key_returns_400(self) -> None:
        # arrange - message present but missing 'text'; pydantic validation fails
        broken_body = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                # 'text' deliberately omitted
                "from": {"username": "alice"},
                "chat": {"id": 1, "type": "private"},
            },
        }
        event = _make_event(broken_body)

        # act
        result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 400
        assert "Invalid payload" in result["body"]

    def test_lambda_handler_unhandled_exception_returns_500(self) -> None:
        # arrange - force an unexpected error after json parsing
        event = _make_event(VALID_TELEGRAM_BODY)

        # act
        with patch("lambda_function.TelegramUpdateModel.model_validate", side_effect=RuntimeError("boom")):
            result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 500
        assert "Internal server error" in result["body"]


# ---------------------------------------------------------------------------
# publishing behaviour
# ---------------------------------------------------------------------------

class TestLambdaHandlerPublishing:
    def test_lambda_handler_valid_telegram_body_calls_asyncio_run(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)

        # act
        with patch("lambda_function.asyncio.run", side_effect=_close_coro) as mock_run:
            lambda_handler(event, {})

        # assert
        mock_run.assert_called_once()

    def test_lambda_handler_publishes_incoming_telegram_message_event_type(
        self,
    ) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act - run the real coroutine so publish is actually awaited
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        mock_publish.assert_awaited_once()
        event_type, _ = mock_publish.call_args.args
        assert event_type == EventType.INCOMING_USER_MESSAGE

    def test_lambda_handler_publishes_dto_with_correct_message_id(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        _, dto = mock_publish.call_args.args
        assert isinstance(dto, TelegramMessageDTO)
        assert dto.message_id == VALID_TELEGRAM_BODY["message"]["message_id"]

    def test_lambda_handler_publishes_dto_with_correct_chat_id(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        _, dto = mock_publish.call_args.args
        assert dto.chat_id == VALID_TELEGRAM_BODY["message"]["chat"]["id"]

    def test_lambda_handler_publishes_dto_with_correct_text(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        _, dto = mock_publish.call_args.args
        assert dto.text == VALID_TELEGRAM_BODY["message"]["text"]

    def test_lambda_handler_publishes_dto_with_correct_username(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        _, dto = mock_publish.call_args.args
        assert dto.username == VALID_TELEGRAM_BODY["message"]["from"]["username"]

    def test_lambda_handler_publishes_dto_with_correct_timestamp(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        _, dto = mock_publish.call_args.args
        assert dto.timestamp == VALID_TELEGRAM_BODY["message"]["date"]

    def test_lambda_handler_publishes_dto_with_message_as_raw_payload(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)
        mock_publish = AsyncMock()

        # act
        with patch("lambda_function.async_event_bus.publish", mock_publish):
            with patch("lambda_function.asyncio.run", side_effect=_run_coro):
                lambda_handler(event, {})

        # assert
        _, dto = mock_publish.call_args.args
        assert dto.raw_payload == VALID_TELEGRAM_BODY["message"]

    def test_lambda_handler_body_without_update_id_does_not_call_asyncio_run(
        self,
    ) -> None:
        # arrange
        event = _make_event({"irrelevant": True})

        # act
        with patch("lambda_function.asyncio.run") as mock_run:
            lambda_handler(event, {})

        # assert
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------

class TestLambdaHandlerLogging:
    def test_lambda_handler_logs_incoming_request(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # arrange
        event = _make_event({})

        # act
        with caplog.at_level(logging.INFO, logger="lambda_function"):
            result = lambda_handler(event, {})

        # assert
        assert result["statusCode"] == 200
        assert any("incoming request" in r.message for r in caplog.records)

    def test_lambda_handler_logs_error_on_invalid_json(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # arrange
        event = {"body": "{{bad json"}

        # act
        with caplog.at_level(logging.ERROR, logger="lambda_function"):
            lambda_handler(event, {})

        # assert
        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_lambda_handler_logs_error_on_unhandled_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)

        # act
        with patch("lambda_function.TelegramUpdateModel.model_validate", side_effect=RuntimeError("boom")):
            with caplog.at_level(logging.ERROR, logger="lambda_function"):
                lambda_handler(event, {})

        # assert
        assert any(r.levelno == logging.ERROR for r in caplog.records)

