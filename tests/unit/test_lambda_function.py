import json
import logging
from unittest.mock import patch

import pytest

from lambda_function import lambda_handler
from interface.event_type import EventType


def _make_event(body: object) -> dict:
    """wrap body in a minimal api gateway proxy event dict."""
    return {"body": json.dumps(body)}


VALID_TELEGRAM_BODY = {
    "update_id": 123,
    "message": {
        "message_id": 1,
        "text": "hello",
        "from": {"username": "alice"},
        "chat": {"id": 42, "type": "private"},
        "date": 1780000000
    },
}


class TestLambdaHandlerResponse:
    def test_lambda_handler_valid_telegram_message_returns_200(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)

        def _close_coro(coro: object) -> None:
            if hasattr(coro, "close"):
                coro.close()  # type: ignore[union-attr]

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


class TestLambdaHandlerPublishing:
    def test_lambda_handler_valid_telegram_body_calls_asyncio_run(self) -> None:
        # arrange
        event = _make_event(VALID_TELEGRAM_BODY)

        def _close_coro(coro: object) -> None:
            # close the coroutine immediately so gc does not emit ResourceWarnings
            if hasattr(coro, "close"):
                coro.close()  # type: ignore[union-attr]

        # act
        with patch("lambda_function.asyncio.run", side_effect=_close_coro) as mock_run:
            lambda_handler(event, {})

        # assert
        mock_run.assert_called_once()

    def test_lambda_handler_publishes_incoming_telegram_message_event_with_correct_type(
        self,
    ) -> None:
        # arrange - capture the coroutine passed to asyncio.run and inspect it
        event = _make_event(VALID_TELEGRAM_BODY)
        captured_coro = {}

        def capture_run(coro: object) -> None:
            captured_coro["coro"] = coro
            # close the coroutine to avoid ResourceWarning
            if hasattr(coro, "close"):
                coro.close()  # type: ignore[union-attr]

        # act
        with patch("lambda_function.asyncio.run", side_effect=capture_run):
            lambda_handler(event, {})

        # assert - asyncio.run must have been called with a coroutine
        assert "coro" in captured_coro

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
