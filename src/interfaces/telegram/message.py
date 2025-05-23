from telegram import Update


class TelegramMessage:
    """
    Plain Old Class Object (POCO) for Telegram messages.
    Extracts relevant information from a Telegram Update object.
    """

    def __init__(self, update: Update):
        self._update: Update = update
        self.userid: int = None
        self.username: str = None
        self.user_fullname: str = None
        self.text: str = None
        self.chatid: int = None
        self.chat_type: str = None
        self.is_group_chat: bool = False
        self.is_private_chat: bool = False

        # Extract user information
        if update.effective_user:
            self.userid = update.effective_user.id
            self.username = update.effective_user.username
            self.user_fullname = (
                f"{update.effective_user.first_name} {update.effective_user.last_name}"
            )

        # Extract message information
        if update.message and update.message.text:
            self.text = update.message.text

        # Extract chat information
        if update.effective_chat:
            self.chatid = update.effective_chat.id
            self.chat_type = update.effective_chat.type
            self.is_group_chat = (
                True if self.chat_type in ["group", "supergroup"] else False
            )
            self.is_private_chat = (
                True
                if self.chat_type not in ["group", "supergroup", "channel"]
                else False
            )

    def __str__(self) -> str:
        """String representation of the message."""
        return f"User: {self._update.effective_user}, Chat: {self._update.effective_chat}, Message: {self.text}"
