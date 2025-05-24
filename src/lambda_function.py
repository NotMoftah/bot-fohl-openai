import os
import json
import asyncio
import logging
from typing import Dict, Any

from core.context import UserContextManager
from interfaces.openai import OpenAIChatBot, OpenAIConfig
from interfaces.telegram import TelegramInterface, TelegramMessage, LambdaRequestParser
from mcp import ToolRegistry, GetTimeTool, HttpRequestTool


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Initialize the context manager
user_context_manager = UserContextManager()


# Initialize the mcp registry
mcp_registry = ToolRegistry()
mcp_registry.register_tool(GetTimeTool())
mcp_registry.register_tool(HttpRequestTool())


# Initialize the OpenAI interface
def init_openai_chatbot():
    gpt_token = os.getenv("GPT_TOKEN")
    if not gpt_token:
        logger.error("GPT_TOKEN environment variable not set")
        raise ValueError("GPT_TOKEN environment variable not set")
    logger.info("Initializing OpenAIChatBot with GPT_TOKEN and config")

    # Create configuration
    config = OpenAIConfig(
        model=os.getenv("GPT_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("GPT_TEMPERATURE", "0.8")),
        system_message=os.getenv(
            "GPT_SYSTEM_MESSAGE",
            "You are a helpful assistant that always responds in raw text format.",
        ),
    )

    # Create chatbot
    chatbot = OpenAIChatBot(
        api_key=gpt_token,
        context_manager=user_context_manager,
        config=config,
        tool_registry=mcp_registry,
    )
    logger.info("OpenAIChatBot initialized: %s", chatbot)
    return chatbot


# Initialize the Telegram interface
def init_telegram_interface():
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set")
        raise ValueError("BOT_TOKEN environment variable not set")
    logger.info("Initializing TelegramInterface with BOT_TOKEN")

    chatbot = init_openai_chatbot()

    # Create Telegram interface
    telegram = TelegramInterface(bot_token)

    # Register message handler
    async def on_message(message: TelegramMessage) -> str:
        try:
            logger.info(
                "Received Telegram message from user %s: %s",
                message.userid,
                message.text,
            )
            response = await chatbot.send_message(str(message.userid), message.text)
            logger.info("Response to user %s: %s", message.userid, response)
            return response
        except Exception as e:
            logger.error(f"Error in message handler: {e}", exc_info=True)
            return "Sorry, I encountered an error processing your request."

    telegram.register_message_handler(on_message)
    logger.info("TelegramInterface fully initialized and handler registered")
    return telegram


# Lambda handler function
async def lambda_handler_async(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Lambda handler invoked. Event: %s", event)
    try:
        # Parse the incoming update from Telegram
        body = json.loads(event.get("body", "{}"))
        logger.info(f"Incoming request body: {body}")

        # Get or create the Telegram interface
        telegram = init_telegram_interface()

        # Create Update object from the incoming data
        parser = LambdaRequestParser(telegram.application)
        update = parser.parse(body)

        if not update:
            logger.error("Received invalid update")
            return {"statusCode": 400, "body": "Bad Request"}

        logger.info("Parsed Telegram update: %s", update)

        # Handle the update
        await telegram.handle_update(update)

        logger.info("Update handled successfully")

        # Return success response
        return {"statusCode": 200, "body": "ok"}
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding error: {json_err}", exc_info=True)
        return {"statusCode": 400, "body": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return {"statusCode": 500, "body": f"Error: {e}"}


# Lambda handler entry point
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Lambda handler entry point called")
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(lambda_handler_async(event, context))
    logger.info("Lambda handler completed with result: %s", result)
    return result
