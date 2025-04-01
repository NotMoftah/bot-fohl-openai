from telegram import Update
from telegram.ext import Application


class LambdaRequestParser:
    def __init__(self, application: Application):
        self.application = application

    def parse(self, body: dict) -> Update:
        """
        Get the Telegram Update object from the Lambda event.
        """
        update = None
        if "update_id" in body:
            update = Update.de_json(body, self.application.bot)
        return update
