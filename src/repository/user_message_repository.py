from __future__ import annotations

import logging

from decimal import Decimal
from typing import Any

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from entity.models import ChatMessage
from interface.dynamodb_repository import IUserMessageRepository


class UserMessageRepository(IUserMessageRepository):
    """repository for interacting with the user messages dynamodb table.

    uses chat_id as partition key and timestamp as sort key.
    """
    def __init__(self, table: Any) -> None:
        """initialize repository with a dynamodb table resource."""
        self._table = table
        self._logger = logging.getLogger(self.__class__.__name__)

    def save(self, chat_message: ChatMessage) -> bool:
        """persist a user message to dynamodb."""
        try:
            item = {
                "chat_id": str(chat_message.chat_id),
                "timestamp": chat_message.timestamp,
                "message_id": chat_message.message_id,
                "username": chat_message.username,
                "text": chat_message.text,
                "chat_type": chat_message.chat_type,
                "raw_payload": chat_message.raw_payload,
            }
            self._table.put_item(Item=item)
            return True
        except ClientError as exc:
            self._logger.error(
                f"failed to save message {chat_message.message_id} for chat {chat_message.chat_id}: {exc}",
                extra={"chat_id": chat_message.chat_id, "message_id": chat_message.message_id},
            )
            return False

    def get_by_chat_id(self, chat_id: int) -> list[ChatMessage]:
        """query all messages for a specific chat."""
        try:
            response = self._table.query(
                KeyConditionExpression=Key("chat_id").eq(str(chat_id))
            )
            items = response.get("Items", [])
            return [self._to_chat_message(item) for item in items]
        except ClientError as exc:
            self._logger.error(
                f"failed to query messages for chat {chat_id}: {exc}",
                extra={"chat_id": chat_id},
            )
            return []

    def get_by_chat_id_in_range(
        self, chat_id: int, timestamp_low: int, timestamp_high: int
    ) -> list[ChatMessage]:
        """query messages for a specific chat within a unix timestamp range."""
        try:
            response = self._table.query(
                KeyConditionExpression=Key("chat_id").eq(str(chat_id))
                & Key("timestamp").between(timestamp_low, timestamp_high)
            )
            items = response.get("Items", [])
            return [self._to_chat_message(item) for item in items]
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

    def _to_chat_message(self, item: dict[str, Any]) -> ChatMessage:
        """map a dynamodb item dict to a ChatMessage dataclass.

        converts decimal types returned by the boto3 resource before mapping,
        since dynamodb stores all numbers as Decimal.
        """
        converted: dict[str, Any] = self._convert_decimals(item)
        return ChatMessage(
            message_id=int(converted["message_id"]) if converted.get("message_id") is not None else None,
            chat_id=int(converted["chat_id"]),
            username=str(converted["username"]),
            text=str(converted["text"]),
            chat_type=str(converted["chat_type"]),
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
