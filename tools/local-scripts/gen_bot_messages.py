import os
import sys
import datetime

import boto3

from entity.models import BotMessage
from repository.bot_message_repository import BotMessageRepository


def main() -> None:
    """read credentials from environment and query the dynamodb table."""
    # region and table name from environment
    table_name = os.environ.get("DYNAMODB_TABLE", "")
    region = os.environ.get("AWS_REGION", "eu-central-1")
    chat_id = 579254966

    if not table_name:
        print("error: DYNAMODB_TABLE variable not set.")
        sys.exit(1)

    # uses local credentials from ~/.aws/credentials or environment variables
    # (e.g., AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    repo = BotMessageRepository(table)

    # example params - modify these for your manual test
    print(f"inserting into table '{table_name}' in region '{region}' for chat {chat_id}...")

    try:
        message = BotMessage(
            chat_id=chat_id,
            timestamp=int(datetime.datetime.now().timestamp()),
            text="Hello from the bot!",
            raw_payload={"example": "payload"}
        )
        result = repo.save(message)
        print("message inserted successfully. Result:", result)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"failed to query dynamodb: {exc}")


if __name__ == "__main__":
    main()
