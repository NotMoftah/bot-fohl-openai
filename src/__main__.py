"""
Local testing script for the Telegram bot.
This allows running the bot locally instead of deploying to AWS Lambda.
"""

import os
import asyncio
import logging
import argparse
from typing import Optional

from dotenv import load_dotenv
from core.context import UserContextManager
from interfaces.openai import OpenAIChatBot, OpenAIConfig
from interfaces.telegram import TelegramInterface
from tools import (
    ToolRegistry,
    GetTimeTool,
    HttpRequestTool,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run the bot locally."""
    # Load environment variables from .env file
    load_dotenv()

    # Get required environment variables
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable not set")

    gpt_token = os.getenv("GPT_TOKEN")
    if not gpt_token:
        raise ValueError("GPT_TOKEN environment variable not set")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run the Telegram bot locally")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name")
    parser.add_argument(
        "--temperature", type=float, default=0.8, help="Model temperature"
    )
    args = parser.parse_args()

    # Create shared components
    user_context_manager = UserContextManager()
    tool_registry = ToolRegistry()

    # Register tools
    tool_registry.register_tool(GetTimeTool())
    tool_registry.register_tool(HttpRequestTool())

    # Create OpenAI configuration
    openai_config = OpenAIConfig(
        model=args.model,
        temperature=args.temperature,
        system_message=os.getenv(
            "GPT_SYSTEM_MESSAGE",
            "You are a helpful assistant that always responds in raw text format.",
        ),
    )

    # Create OpenAI chatbot
    chatbot = OpenAIChatBot(
        api_key=gpt_token,
        context_manager=user_context_manager,
        config=openai_config,
        tool_registry=tool_registry,
    )

    # Create Telegram interface
    telegram = TelegramInterface(bot_token)

    # Register message handler
    async def on_message(message):
        try:
            # Use user_id from message for context
            return await chatbot.send_message(str(message.userid), message.text)
        except Exception as e:
            logger.error(f"Error in message handler: {e}", exc_info=True)
            return "Sorry, I encountered an error processing your request."

    telegram.register_message_handler(on_message)

    # Start the bot
    logger.info("Starting the bot...")

    # Initialize application
    await telegram.application.initialize()

    # Start receiving updates
    await telegram.application.start_polling()
    logger.info("Bot is now running. Press Ctrl+C to stop.")

    # Run until interrupted
    try:
        await telegram.application.updater.stop_signals.wait()
    finally:
        logger.info("Stopping the bot...")
        await telegram.application.stop()


if __name__ == "__main__":
    asyncio.run(main())
