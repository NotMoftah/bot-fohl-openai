import os
import json
import asyncio
import logging
from typing import Any

from pydantic import ValidationError

from entity.dto import TelegramMessageDTO
from entity.models import TelegramUpdateModel
from handler.incoming_telegram_messages_handler import IncomingTelegramMessagesHandler
from handler.send_telegram_messages_handler import SendTelegramMessagesHandler
from interface.event_type import EventType
from utils.event_bus import async_event_bus


logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("lambda_function")

BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")

# handlers are singletons registering once at cold-start avoids re-subscription
IncomingTelegramMessagesHandler().init(async_event_bus)
SendTelegramMessagesHandler(BOT_TOKEN).init(async_event_bus)


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
            )
            asyncio.run(publish_async(EventType.INCOMING_TELEGRAM_MESSAGE, telegram_message))

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
