import logging

from typing import Callable, Awaitable
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from .poco import TelegramMessage


class FohlFehBot:
    def __init__(self, bot_token: str):
        self.application_initialized = False
        self.application = ApplicationBuilder().token(bot_token).build()
        self.logger = logging.getLogger(self.__class__.__name__)
        # register handlers
        self.handlers: dict[str, Callable[[TelegramMessage], Awaitable[str]]] = {}
        self._add_handlers()

    def add_private_message_handler(
        self, delegate_function: Callable[[TelegramMessage], Awaitable[str]]
    ):
        self.handlers["private_message"] = delegate_function
        self.logger.info("Added private message handler")

    async def handle_update_async(self, update: Update) -> None:
        """
        Process an update asynchronously.
        """
        try:
            if not self.application_initialized:
                await self.application.initialize()
                self.application_initialized = True
                self.logger.info("Application initialized")

            self.logger.debug(f"Received update: {update}")
            await self.application.process_update(update)
        except Exception as e:
            self.logger.error(f"Error in handle_update_async: {e}", exc_info=True)

    def _add_handlers(self):
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_private_message)
        )

    async def _on_private_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Echo the user message.
        """
        try:
            async_handler = self.handlers.get("private_message", None)

            # check if there's a handler for private messages
            if async_handler is None:
                return

            message = TelegramMessage(update)
            if message.is_private_chat:
                self.logger.debug(f"Received message: {message}")
                replay_message = await async_handler(message)
                self.logger.debug(f"Received replay: {replay_message}")
                await update.message.reply_text(replay_message)
        except Exception as e:
            self.logger.error(
                f"Error in _on_private_message handler: {e}", exc_info=True
            )
