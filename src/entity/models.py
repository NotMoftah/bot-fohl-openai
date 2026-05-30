from __future__ import annotations

import dataclasses

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ChatMessage:
    """immutable carrier for a single chat message payload."""

    message_id: Optional[int]
    chat_id: int
    username: str
    text: str
    chat_type: str  # plain str as telegram may send values outside ChatType
    timestamp: int = 0
    raw_payload: dict[str, object] = dataclasses.field(default_factory=dict)

    def serialize(self) -> dict[str, object]:
        """return a json-serializable dict of all dto fields."""
        return dataclasses.asdict(self)
