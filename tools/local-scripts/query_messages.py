import json
import os
import sys

import boto3

from dataclasses import asdict

from repository.user_message_repository import UserMessageRepository


def main() -> None:
    """read credentials from environment and query the dynamodb table."""
    # region and table name from environment
    user_messages_table_name = os.environ.get("TABLE_USER_MSG")
    region = os.environ.get("AWS_REGION")
    chat_id = int(os.environ.get("CHAT_ID"))

    if not user_messages_table_name:
        print("error: DYNAMODB_TABLE variable not set.")
        sys.exit(1)

    # uses local credentials from ~/.aws/credentials or environment variables
    # (e.g., AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(user_messages_table_name)
    repo = UserMessageRepository(table)

    # example params - modify these for your manual test
    print(f"querying table '{user_messages_table_name}' in region '{region}' for chat {chat_id}...")

    try:
        messages = repo.get_by_chat_id(chat_id=chat_id)
        print(f"found {len(messages)} messages:")
        for message in messages:
            clean_dict = {k: v for k, v in asdict(message).items() if k != 'raw_payload'}
            print(json.dumps(clean_dict, indent=4))
    except Exception as exc:  # pylint: disable=broad-except
        print(f"failed to query dynamodb: {exc}")


if __name__ == "__main__":
    main()
