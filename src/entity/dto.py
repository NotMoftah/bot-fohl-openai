from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


class ChatType(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


@dataclass
class TelegramMessageDTO:
    """immutable carrier for a single telegram message payload."""

    message_id: Optional[int]
    chat_id: int
    username: str
    text: str
    chat_type: str  # plain str — telegram may send values outside ChatType

    def serialize(self) -> dict[str, object]:
        """return a json-serialisable dict of all dto fields."""
        return dataclasses.asdict(self)
