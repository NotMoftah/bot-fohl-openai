import pytest

from pydantic import ValidationError

from entity.telegram import (
    TelegramChatModel,
    TelegramFromModel,
    TelegramMessageModel,
    TelegramUpdateModel,
)


VALID_UPDATE = {
    "update_id": 1,
    "message": {
        "message_id": 10,
        "text": "hi",
        "from": {"username": "alice"},
        "chat": {"id": 42, "type": "private"},
        "date": 1780000000
    },
}


class TestTelegramFromModel:
    def test_telegram_from_model_parses_username(self) -> None:
        # arrange / act
        model = TelegramFromModel(username="alice")

        # assert
        assert model.username == "alice"

    def test_telegram_from_model_rejects_missing_username(self) -> None:
        # arrange / act / assert
        with pytest.raises(ValidationError):
            TelegramFromModel.model_validate({})


class TestTelegramChatModel:
    def test_telegram_chat_model_parses_id_and_type(self) -> None:
        # arrange / act
        model = TelegramChatModel(id=42, type="private")

        # assert
        assert model.id == 42
        assert model.type == "private"

    def test_telegram_chat_model_rejects_missing_id(self) -> None:
        # arrange / act / assert
        with pytest.raises(ValidationError):
            TelegramChatModel.model_validate({"type": "private"})


class TestTelegramMessageModel:
    def test_telegram_message_model_parses_valid_payload(self) -> None:
        # arrange
        raw = {
            "message_id": 10,
            "text": "hello",
            "from": {"username": "bob"},
            "chat": {"id": 5, "type": "group"},
            "date": 1780000000
        }

        # act
        model = TelegramMessageModel.model_validate(raw)

        # assert
        assert model.message_id == 10
        assert model.text == "hello"
        assert model.from_.username == "bob"
        assert model.chat.id == 5

    def test_telegram_message_model_rejects_missing_text(self) -> None:
        # arrange
        raw = {
            "message_id": 1,
            "from": {"username": "bob"},
            "chat": {"id": 5, "type": "private"},
        }

        # act / assert
        with pytest.raises(ValidationError):
            TelegramMessageModel.model_validate(raw)

    def test_telegram_message_model_rejects_missing_from(self) -> None:
        # arrange
        raw = {
            "message_id": 1,
            "text": "hi",
            "chat": {"id": 5, "type": "private"},
        }

        # act / assert
        with pytest.raises(ValidationError):
            TelegramMessageModel.model_validate(raw)


class TestTelegramUpdateModel:
    def test_telegram_update_model_parses_valid_update(self) -> None:
        # arrange / act
        model = TelegramUpdateModel.model_validate(VALID_UPDATE)

        # assert
        assert model.update_id == 1
        assert model.message.message_id == 10
        assert model.message.from_.username == "alice"
        assert model.message.chat.id == 42
        assert model.message.chat.type == "private"

    def test_telegram_update_model_rejects_missing_message(self) -> None:
        # arrange / act / assert
        with pytest.raises(ValidationError):
            TelegramUpdateModel.model_validate({"update_id": 1})

    def test_telegram_update_model_rejects_missing_update_id(self) -> None:
        # arrange / act / assert
        with pytest.raises(ValidationError):
            TelegramUpdateModel.model_validate({"message": VALID_UPDATE["message"]})

