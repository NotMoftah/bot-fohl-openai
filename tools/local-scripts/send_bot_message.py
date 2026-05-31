import asyncio
import os

from telegram import Bot


chat_id = int(os.environ.get("CHAT_ID"))
telegram_token = os.environ.get("TELEGRAM_TOKEN")

message = "..."


async def main() -> None:
    async with Bot(token=telegram_token) as bot:
        await bot.send_message(chat_id=chat_id, text=message)


asyncio.run(main())
