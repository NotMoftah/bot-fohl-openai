import json
import logging
import os

import boto3
import humanize

from datetime import datetime, timezone

from openai import OpenAI

from entity.models import BotMessage, ChatMessage
from repository.bot_message_repository import BotMessageRepository
from repository.user_message_repository import UserMessageRepository


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# env vars
user_messages_table_name = os.environ.get("TABLE_USER_MSG")
bot_messages_table_name = os.environ.get("TABLE_BOT_MSG")
region = os.environ.get("AWS_REGION")
chat_id = int(os.environ.get("CHAT_ID"))

# load llm prompt and structured output schema
llm_system_prompt_path = "llm-system-prompt.md"
structured_output_schema_path = "structured-output-schema.json"
with open(llm_system_prompt_path, "r") as f:
    llm_system_prompt = f.read()
with open(structured_output_schema_path, "r") as f:
    structured_output_schema: dict = json.load(f)


def format_message_for_prompt(message: ChatMessage) -> str:
    """format a single ChatMessage into the structured text block fed to the AI."""
    iso_ts = datetime.fromtimestamp(message.timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
    return (f"username: {message.username}\n"
            f"timestamp: {iso_ts}\n"
            f"message: {message.text}")


def build_ai_messages(system_prompt: str, user_messages: list[ChatMessage]) -> list[dict]:
    """build the openai messages list: one system entry followed by one user entry per message."""
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"the current time is: "
                                      f"{datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M')}. "
                                      f"Use this current time for any time calculations or comparisons."},
    ]
    for msg in user_messages:
        messages.append({"role": "user", "content": format_message_for_prompt(msg)})
    return messages


def main() -> None:
    client = OpenAI(
        base_url="http://127.0.0.1:1234/v1",
        api_key="lm-studio"
    )

    # list models
    available_models = client.models.list()
    logger.info(f"Available models: {available_models}")

    # db access
    dynamodb = boto3.resource("dynamodb", region_name=region)
    user_messages_table = dynamodb.Table(user_messages_table_name)
    bot_messages_table = dynamodb.Table(bot_messages_table_name)
    user_messages_repo = UserMessageRepository(user_messages_table)
    bot_messages_repo = BotMessageRepository(bot_messages_table)

    # load all user messages for the chat from dynamodb
    user_messages = user_messages_repo.get_by_chat_id(chat_id)
    logger.info(f"Loaded {len(user_messages)} user messages for chat_id {chat_id}.")

    if not user_messages:
        logger.info(f"No user messages found for chat_id {chat_id}, nothing to process.")
        return

    user_content = build_ai_messages(llm_system_prompt, user_messages)

    # stream=False is required for structured output to parse the full response
    completion = client.chat.completions.create(
        model="local-model",
        messages=user_content,
        temperature=0.7,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": structured_output_schema["title"],
                "schema": structured_output_schema,
                "strict": True,
            },
        },
    )


    response_text: str = completion.choices[0].message.content
    response_json = json.loads(response_text)
    commands = response_json["commands"]
    for command in commands:
        command_name = command["command"]
        command_parameters = command["parameters"]
        if command_name == "Reminder":
            remainder_timestamp, remainder_text = command_parameters
            dt_object = datetime.fromisoformat(remainder_timestamp).astimezone(tz=timezone.utc)
            relative_time = humanize.naturaltime(datetime.now(tz=timezone.utc) - dt_object)
            bot_message = BotMessage(
                chat_id=chat_id,
                timestamp=int(dt_object.timestamp()),
                text=f"[UTC] {dt_object.strftime('%Y-%m-%dT%H:%M')} ({relative_time}) \n\n"
                     f"{remainder_text} \n"
                     f"---",
                raw_payload=command,
            )
            bot_messages_repo.save(bot_message)


if __name__ == "__main__":
    main()
