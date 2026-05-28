
class TelegramMessageDTO:
    def __init__(self, message_id, chat_id, username, text, chat_type):
        self.message_id : int = message_id
        self.chat_id : int = chat_id
        self.username : int = username
        self.text : str = text
        self.chat_type: str = chat_type

    def __str__(self):
        return (f"TelegramMessage("
                f"message_id={self.message_id}, "
                f"chat_id={self.chat_id}, "
                f"chat_type={self.chat_type}, "
                f"username={self.username}, "
                f"text={self.text})")

    def serialize(self) -> dict:
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "chat_type": self.chat_type,
            "username": self.username,
            "text": self.text
        }