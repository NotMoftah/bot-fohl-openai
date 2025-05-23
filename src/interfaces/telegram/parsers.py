from telegram import Update
from telegram.ext import Application


class LambdaRequestParser:
    """
    Parser to convert AWS Lambda requests to Telegram Update objects.
    """

    def __init__(self, application: Application):
        """
        Initialize the parser.

        Args:
            application: The Telegram application instance
        """
        self.application = application

    def parse(self, body: dict) -> Update:
        """
        Parse a Lambda request body into a Telegram Update object.

        Args:
            body: The request body from the Lambda event

        Returns:
            A Telegram Update object, or None if the body is invalid
        """
        update = None
        if "update_id" in body:
            update = Update.de_json(body, self.application.bot)
        return update
