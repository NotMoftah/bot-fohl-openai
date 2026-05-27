import os
import json
import asyncio

from utils import LambdaLogger
from telegram_bot import TelegramMessage, FohlFehBot, LambdaRequestParser

# Set up logging
logger = LambdaLogger()

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def on_private_message(message: TelegramMessage) -> str:
    return message.text


# Initialize the bot
bot = FohlFehBot(BOT_TOKEN)
bot.add_private_message_handler(on_private_message)


def lambda_handler(event, context):
    try:
        # Parse the incoming update from Telegram
        body = json.loads(event.get("body", "{}"))
        logger.info(f"Incoming request body: {body}")

        # Create Update object from the incoming data
        parser = LambdaRequestParser(bot.application)
        update = parser.parse(body)

        if not update:
            logger.error("Received invalid update")
            return {"statusCode": 400, "body": "Bad Request"}

        # Handle the update asynchronously
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.handle_update_async(update))

        # Return success response
        return {"statusCode": 200, "body": "ok"}
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding error: {json_err}", exc_info=True)
        return {"statusCode": 400, "body": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return {"statusCode": 500, "body": f"Error: {e}"}
