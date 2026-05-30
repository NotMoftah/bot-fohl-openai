import os
import json
import asyncio
import logging

import boto3

from typing import Any

from pydantic import ValidationError

from entity.dto import TelegramMessageDTO
from entity.telegram import TelegramUpdateModel
from handler.incoming_telegram_message_handler import IncomingTelegramMessageHandler
from handler.outgoing_telegram_message_handler import OutgoingTelegramMessageHandler
from interface.enum_type import EventType
from repository.user_message_repository import UserMessageRepository
from repository.bot_message_repository import BotMessageRepository
from utils.event_bus import async_event_bus


logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("lambda_function")

# env vars
BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
TABLE_USER_MESSAGES: str | None = os.getenv("DYNAMODB_TABLE_USER_MESSAGES")
TABLE_BOT_MESSAGES: str | None = os.getenv("DYNAMODB_TABLE_BOT_MESSAGES")

# dynamodb
DYNAMODB = boto3.resource("dynamodb")
user_messages_table = DYNAMODB.Table(TABLE_USER_MESSAGES)
bot_messages_table = DYNAMODB.Table(TABLE_BOT_MESSAGES)

# repositories
user_messages_repository = UserMessageRepository(user_messages_table)
bot_messages_repository = BotMessageRepository(bot_messages_table)

# handlers are singletons registering once at cold-start avoids re-subscription
IncomingTelegramMessageHandler(user_messages_repository).init(async_event_bus)
OutgoingTelegramMessageHandler(BOT_TOKEN).init(async_event_bus)


async def publish_async(event_type: EventType, data: Any) -> None:
    """thin coroutine wrapper so asyncio.run has a single awaitable to run."""
    await async_event_bus.publish(event_type, data)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """parse the api gateway payload and fan-out to registered event handlers.

    returns a minimal api gateway proxy response as telegram only requires 200 ok.
    """
    try:
        body: dict[str, Any] = json.loads(event.get("body", "{}"))
        logger.info(f"incoming request received (keys={list(body.keys())})")

        if "update_id" in body and "message" in body:
            update = TelegramUpdateModel.model_validate(body)
            telegram_message = TelegramMessageDTO(
                message_id=update.message.message_id,
                text=update.message.text,
                chat_id=update.message.chat.id,
                chat_type=update.message.chat.type,
                username=update.message.from_.username,
                timestamp=update.message.date,
                raw_payload=body.get("message", {}),
            )
            asyncio.run(publish_async(EventType.INCOMING_USER_MESSAGE, telegram_message))

        return {"statusCode": 200, "body": "ok"}

    except json.JSONDecodeError as exc:
        logger.error(f"json decoding error: {exc}", exc_info=True)
        return {"statusCode": 400, "body": "Invalid JSON format"}

    except ValidationError as exc:
        logger.error(f"telegram payload validation failed: {exc}", exc_info=True)
        return {"statusCode": 400, "body": "Invalid payload structure"}

    except Exception as exc:  # noqa: BLE001 last-resort lambda safety net
        logger.error(f"unhandled error in lambda_handler: {exc}", exc_info=True)
        return {"statusCode": 500, "body": "Internal server error"}
