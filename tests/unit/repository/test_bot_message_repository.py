from __future__ import annotations

import boto3
import pytest

from moto import mock_aws
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from entity.models import BotMessage
from repository.bot_message_repository import BotMessageRepository


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_TABLE_NAME = "bot-messages"
_CHAT_ID = 42


def _make_message(
    chat_id: int = _CHAT_ID,
    text: str = "hello",
    timestamp: int = 1_780_000_000,
) -> BotMessage:
    return BotMessage(
        chat_id=chat_id,
        text=text,
        timestamp=timestamp,
        raw_payload={"source": "bot"},
    )


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def dynamodb_table():
    """provide a real moto-backed dynamodb table for the duration of each test."""
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="eu-west-1")
        table = resource.create_table(
            TableName=_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "chat_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "chat_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "N"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


@pytest.fixture()
def repo(dynamodb_table) -> BotMessageRepository:
    return BotMessageRepository(table=dynamodb_table)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

class TestSave:
    def test_save_valid_message_returns_true(self, repo: BotMessageRepository) -> None:
        # arrange
        message = _make_message()

        # act
        result = repo.save(message)

        # assert
        assert result is True

    def test_save_valid_message_persists_item(
        self, repo: BotMessageRepository, dynamodb_table
    ) -> None:
        # arrange
        message = _make_message(text="persisted")

        # act
        repo.save(message)

        # assert
        response = dynamodb_table.get_item(
            Key={"chat_id": str(_CHAT_ID), "timestamp": 1_780_000_000}
        )
        assert response["Item"]["text"] == "persisted"
        assert int(response["Item"]["chat_id"]) == _CHAT_ID

    def test_save_persists_raw_payload(
        self, repo: BotMessageRepository, dynamodb_table
    ) -> None:
        # arrange
        message = _make_message()

        # act
        repo.save(message)

        # assert
        response = dynamodb_table.get_item(
            Key={"chat_id": str(_CHAT_ID), "timestamp": 1_780_000_000}
        )
        assert response["Item"]["raw_payload"] == {"source": "bot"}

    def test_save_on_client_error_returns_false(self) -> None:
        # arrange
        mock_table = MagicMock()
        mock_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "throttled"}},
            "PutItem",
        )
        repo = BotMessageRepository(table=mock_table)
        message = _make_message()

        # act
        result = repo.save(message)

        # assert
        assert result is False


# ---------------------------------------------------------------------------
# get_by_chat_id
# ---------------------------------------------------------------------------

class TestGetByChatId:
    def test_get_by_chat_id_returns_bot_message_instances(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(timestamp=1_000))
        repo.save(_make_message(timestamp=2_000))

        # act
        results = repo.get_by_chat_id(_CHAT_ID)

        # assert
        assert all(isinstance(r, BotMessage) for r in results)

    def test_get_by_chat_id_returns_correct_field_values(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(text="bot reply", timestamp=3_000))

        # act
        results = repo.get_by_chat_id(_CHAT_ID)

        # assert
        assert len(results) == 1
        msg = results[0]
        assert msg.chat_id == _CHAT_ID
        assert msg.text == "bot reply"
        assert msg.timestamp == 3_000

    def test_get_by_chat_id_returns_multiple_messages(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(timestamp=1_000))
        repo.save(_make_message(timestamp=2_000))

        # act
        results = repo.get_by_chat_id(_CHAT_ID)

        # assert
        assert len(results) == 2

    def test_get_by_chat_id_returns_empty_list_when_no_items(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange - table is empty

        # act
        results = repo.get_by_chat_id(999)

        # assert
        assert results == []

    def test_get_by_chat_id_on_client_error_returns_empty_list(self) -> None:
        # arrange
        mock_table = MagicMock()
        mock_table.query.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "table not found"}},
            "Query",
        )
        repo = BotMessageRepository(table=mock_table)

        # act
        results = repo.get_by_chat_id(_CHAT_ID)

        # assert
        assert results == []


# ---------------------------------------------------------------------------
# get_by_chat_id_in_range
# ---------------------------------------------------------------------------

class TestGetByChatIdInRange:
    def test_get_by_chat_id_in_range_returns_only_messages_within_range(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(timestamp=1_000))
        repo.save(_make_message(timestamp=5_000))
        repo.save(_make_message(timestamp=9_000))

        # act
        results = repo.get_by_chat_id_in_range(_CHAT_ID, 2_000, 8_000)

        # assert
        assert len(results) == 1
        assert results[0].timestamp == 5_000

    def test_get_by_chat_id_in_range_returns_bot_message_instances(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(timestamp=1_000))

        # act
        results = repo.get_by_chat_id_in_range(_CHAT_ID, 500, 2_000)

        # assert
        assert all(isinstance(r, BotMessage) for r in results)

    def test_get_by_chat_id_in_range_returns_correct_field_values(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(text="scheduled action", timestamp=4_000))

        # act
        results = repo.get_by_chat_id_in_range(_CHAT_ID, 3_000, 5_000)

        # assert
        assert len(results) == 1
        msg = results[0]
        assert msg.chat_id == _CHAT_ID
        assert msg.text == "scheduled action"
        assert msg.timestamp == 4_000

    def test_get_by_chat_id_in_range_returns_empty_list_when_no_items_in_range(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange
        repo.save(_make_message(timestamp=1_000))

        # act
        results = repo.get_by_chat_id_in_range(_CHAT_ID, 5_000, 9_000)

        # assert
        assert results == []

    def test_get_by_chat_id_in_range_includes_boundary_timestamps(
        self, repo: BotMessageRepository
    ) -> None:
        # arrange - items exactly on the range boundaries
        repo.save(_make_message(timestamp=1_000))
        repo.save(_make_message(timestamp=9_000))

        # act
        results = repo.get_by_chat_id_in_range(_CHAT_ID, 1_000, 9_000)

        # assert
        assert len(results) == 2

    def test_get_by_chat_id_in_range_on_client_error_returns_empty_list(self) -> None:
        # arrange
        mock_table = MagicMock()
        mock_table.query.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "table not found"}},
            "Query",
        )
        repo = BotMessageRepository(table=mock_table)

        # act
        results = repo.get_by_chat_id_in_range(_CHAT_ID, 0, 9_999)

        # assert
        assert results == []

