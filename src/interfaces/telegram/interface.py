import logging
from typing import Dict, Callable, Awaitable, Optional

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from .message import TelegramMessage


class TelegramInterface:
    """
    Interface to the Telegram Bot API.
    Handles message processing and dispatch to registered handlers.
    """

    def __init__(self, bot_token: str):
        """
        Initialize the Telegram interface.

        Args:
            bot_token: The Telegram bot token
        """
        self.application = ApplicationBuilder().token(bot_token).build()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.application_initialized = False

        # Message handlers
        self.message_handler: Optional[Callable[[TelegramMessage], Awaitable[str]]] = (
            None
        )

        # Add application handlers
        self._add_handlers()

        self.logger.info("TelegramInterface initialized")

    def register_message_handler(
        self, handler: Callable[[TelegramMessage], Awaitable[str]]
    ) -> None:
        """
        Register a handler for private messages.

        Args:
            handler: Async function that takes a TelegramMessage and returns a string response
        """
        self.message_handler = handler
        self.logger.info("Registered message handler")

    async def handle_update(self, update: Update) -> None:
        """
        Process a Telegram update.

        Args:
            update: The Telegram Update object
        """
        try:
            if not self.application_initialized:
                await self.application.initialize()
                self.application_initialized = True
                self.logger.info("Application initialized")

            self.logger.debug(f"Processing update: {update}")
            await self.application.process_update(update)
        except Exception as e:
            self.logger.error(f"Error in handle_update: {e}", exc_info=True)

    def _add_handlers(self) -> None:
        """Add message handlers to the application."""
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )

    async def _on_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handler for incoming messages.

        Args:
            update: The Telegram Update object
            context: The Telegram context
        """
        try:
            if not self.message_handler:
                self.logger.warning("No message handler registered")
                return

            message = TelegramMessage(update)

            if message.is_private_chat:
                self.logger.debug(f"Received private message: {message}")
                response = await self.message_handler(message)
                await update.message.reply_text(response)
            elif message.is_group_chat:
                # Handle group chat messages if needed
                pass
        except Exception as e:
            self.logger.error(f"Error in message handler: {e}", exc_info=True)
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message."
            )
