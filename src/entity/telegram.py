from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TelegramFromModel(BaseModel):
    username: str


class TelegramChatModel(BaseModel):
    id: int
    type: str


class TelegramMessageModel(BaseModel):
    # alias maps telegram's "from" key (reserved word in python) to from_
    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    date: int
    from_: TelegramFromModel = Field(alias="from")
    chat: TelegramChatModel

    text: str | None = None
    photo: list[Any] | None = None
    caption: str | None = None


class TelegramUpdateModel(BaseModel):
    update_id: int
    message: TelegramMessageModel
