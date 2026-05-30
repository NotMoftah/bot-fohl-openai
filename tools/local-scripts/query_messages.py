import json
import os
import sys

import boto3

from entity.dto import TelegramMessageDTO
from repository.message_repository import MessageRepository


def main() -> None:
    """read credentials from environment and query the dynamodb table."""
    # region and table name from environment
    region = os.environ.get("AWS_REGION", "eu-central-1")
    table_name = os.environ.get("DYNAMODB_TABLE_MESSAGES", "telegram-bot-messages")

    if not table_name:
        print("error: DYNAMODB_TABLE_MESSAGES atmosphere variable not set.")
        sys.exit(1)

    # uses local credentials from ~/.aws/credentials or environment variables
    # (e.g., AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    repo = MessageRepository(table)

    # example params - modify these for your manual test
    chat_id = 123456789
    start_time = 0
    end_time = 2000000000

    print(f"querying table '{table_name}' in region '{region}' for chat {chat_id}...")

    try:
        messages = repo.get_messages_by_range(chat_id, start_time, end_time)
        print(f"found {len(messages)} messages:")
        print(json.dumps(messages, indent=2))
    except Exception as exc:  # pylint: disable=broad-except
        print(f"failed to query dynamodb: {exc}")


if __name__ == "__main__":
    main()
