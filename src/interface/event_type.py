from enum import StrEnum


class EventType(StrEnum):
    """string-valued enum so event types can be used as plain dict keys."""

    INCOMING_TELEGRAM_MESSAGE = "INCOMING_TELEGRAM_MESSAGE"
    INCOMING_TELEGRAM_COMMAND = "INCOMING_TELEGRAM_COMMAND"
    SEND_TELEGRAM_MESSAGE = "SEND_TELEGRAM_MESSAGE"
