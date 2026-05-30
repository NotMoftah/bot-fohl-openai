from enum import StrEnum


class EventType(StrEnum):
    """string-valued enum so event types can be used as plain dict keys."""
    INCOMING_USER_MESSAGE = "INCOMING_USER_MESSAGE"
    INCOMING_USER_COMMAND = "INCOMING_USER_COMMAND"
    SEND_TELEGRAM_MESSAGE = "SEND_TELEGRAM_MESSAGE"


class UserCommandType(StrEnum):
    """string-valued enum so user command types can be used as plain dict keys."""
    LIST_ACTIONS = "LIST_ACTIONS"
    LIST_TODAY_ACTIONS = "LIST_TODAY_ACTIONS"
