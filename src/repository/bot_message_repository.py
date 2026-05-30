from __future__ import annotations

import logging

from decimal import Decimal
from typing import Any

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from entity.models import BotMessage
from interface.dynamodb_repository import IBotMessageRepository


class BotMessageRepository(IBotMessageRepository):
    """repository for interacting with the bot messages dynamodb table.

    uses chat_id as partition key and timestamp as sort key.
    """
    def __init__(self, table: Any) -> None:
        """initialize repository with a dynamodb table resource."""
        self._table = table
        self._logger = logging.getLogger(self.__class__.__name__)

    def save(self, bot_message: BotMessage) -> bool:
        """persist a bot message to dynamodb."""
        try:
            item = {
                "chat_id": str(bot_message.chat_id),
                "timestamp": bot_message.timestamp,
                "text": bot_message.text,
                "raw_payload": bot_message.raw_payload,
            }
            self._table.put_item(Item=item)
            return True
        except ClientError as exc:
            self._logger.error(
                f"failed to save bot message for chat {bot_message.chat_id}: {exc}",
                extra={"chat_id": bot_message.chat_id},
            )
            return False

    def get_by_chat_id(self, chat_id: int) -> list[BotMessage]:
        """query all messages for a specific chat."""
        try:
            response = self._table.query(
                KeyConditionExpression=Key("chat_id").eq(str(chat_id))
            )
            items = response.get("Items", [])
            return [self._to_bot_message(item) for item in items]
        except ClientError as exc:
            self._logger.error(
                f"failed to query messages for chat {chat_id}: {exc}",
                extra={"chat_id": chat_id},
            )
            return []

    def get_by_chat_id_in_range(
        self, chat_id: int, timestamp_low: int, timestamp_high: int
    ) -> list[BotMessage]:
        """query messages for a specific chat within a unix timestamp range."""
        try:
            response = self._table.query(
                KeyConditionExpression=Key("chat_id").eq(str(chat_id))
                & Key("timestamp").between(timestamp_low, timestamp_high)
            )
            items = response.get("Items", [])
            return [self._to_bot_message(item) for item in items]
        except ClientError as exc:
            self._logger.error(
                f"failed to query messages for chat {chat_id} in range {timestamp_low}-{timestamp_high}: {exc}",
                extra={
                    "chat_id": chat_id,
                    "start_time": timestamp_low,
                    "end_time": timestamp_high,
                },
            )
            return []

    def _to_bot_message(self, item: dict[str, Any]) -> BotMessage:
        """map a dynamodb item dict to a BotMessage dataclass.

        converts decimal types returned by the boto3 resource before mapping,
        since dynamodb stores all numbers as Decimal.
        """
        converted: dict[str, Any] = self._convert_decimals(item)
        return BotMessage(
            chat_id=int(converted["chat_id"]),
            text=str(converted["text"]),
            timestamp=int(converted.get("timestamp", 0)),
            raw_payload=converted.get("raw_payload", {}),
        )

    def _convert_decimals(self, obj: Any) -> Any:
        """recursively convert decimal objects to int or float.

        boto3 dynamodb resource returns decimals for all number types.
        """
        if isinstance(obj, list):
            return [self._convert_decimals(i) for i in obj]
        if isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return obj
