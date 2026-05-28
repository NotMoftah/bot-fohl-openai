from enum import StrEnum


class EventType(StrEnum):
    incoming_telegram_message = "INCOMING_TELEGRAM_MESSAGE"
    incoming_telegram_command = "INCOMING_TELEGRAM_COMMAND"
    send_telegram_message = "SEND_TELEGRAM_MESSAGE"
