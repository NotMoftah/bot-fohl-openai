import os
import json
import asyncio
import logging

from entity.dto import TelegramMessageDTO
from handler.incoming_telegram_messages_handler import IncomingTelegramMessagesHandler
from handler.send_telegram_messages_handler import SendTelegramMessagesHandler
from interface.event_type import EventType
from utils.event_bus import async_event_bus

# set up logging
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("lambda_function")

# load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# initialize the handlers
IncomingTelegramMessagesHandler().init(async_event_bus)
SendTelegramMessagesHandler(BOT_TOKEN).init(async_event_bus)

# handle async bus publishing
async def publish_async(event_type, event):
    await async_event_bus.publish(event_type, event)

def lambda_handler(event, context):
    try:
        # parse the incoming data
        body = json.loads(event.get("body", "{}"))
        logger.info(f"Incoming request body: {body}")

        # telegram data contains update_id in body
        if "update_id" in body:
            telegram_message = TelegramMessageDTO(
                message_id=body["message"]["message_id"],
                text=body["message"]["text"],
                chat_id=body["message"]["chat"]["id"],
                username=body["message"]["chat"]["username"],
            )
            asyncio.run(publish_async(EventType.incoming_telegram_message, telegram_message))

        # return success response
        return {"statusCode": 200, "body": "ok"}
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding error: {json_err}", exc_info=True)
        return {"statusCode": 400, "body": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return {"statusCode": 500, "body": f"Error: {e}"}
