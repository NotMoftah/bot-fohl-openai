import json
import logging

from typing import List
from openai import AsyncOpenAI
from core import ExternalToolsHandler


class OpenAIChatBot:
    INSTRUCTIONS: str = (
        """You are a helpful assistant that always responds in raw text format."""
    )

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "clear_history",
                "description": "Clear internal history logs.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }
    ]

    HISTORY_LIMIT = 20

    def __init__(self, api_key: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = AsyncOpenAI(api_key=api_key, timeout=10)
        self.handlers: List[ExternalToolsHandler] = []
        self.tools = list(OpenAIChatBot.TOOLS)
        self.history = [
            {"role": "system", "content": self.INSTRUCTIONS},
        ]
        self.logger.info("BotGPT initialized.")

    def register_external_tools(self, handler: ExternalToolsHandler) -> None:
        # check if the handler is a subclass of ExternalToolsHandler
        if not issubclass(handler.__class__, ExternalToolsHandler):
            raise TypeError("handler must be a subclass of ExternalToolsHandler.")
        # check if the handler is already registered
        # if not, register the handler and add its tools to the list
        if not handler in self.handlers:
            self.handlers.append(handler)
            self.tools.extend(handler.tools)
            self.logger.info("registered external tools handler: %s", handler)

    async def send_message(self, message: str, model: str = "gpt-4o-mini") -> str:
        # add user message to history
        segment = {"role": "user", "content": message}
        self.history.append(segment)
        # log the user message
        self.logger.info("added to history the user message: %s", message)
        response = await self._generate_response(model)
        # trim the history
        self._trim_history()
        return response

    async def _generate_response(self, model="gpt-4o-mini") -> str:
        while True:
            # make request to OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                tools=self.tools,
                messages=self.history,
                n=1,
                temperature=0.8,
                top_p=0.8,
                max_tokens=256,
                frequency_penalty=0,
                presence_penalty=0,
            )

            # break if there are no choices in the response
            if len(response.choices) == 0:
                break

            # add the assistant response to the history
            self.history.append(response.choices[0].message)
            self.logger.info(
                "added to history the assistant response: %s",
                response.choices[0].message.content,
            )

            # check if there are any tool calls in the response
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls is not None and len(tool_calls) > 0:
                for tool_call in response.choices[0].message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    result = self._call_function(name, args)
                    self.logger.info(
                        "ai bot called function %s with args %s", name, args
                    )
                    # print a useful log message
                    self.history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )
                    self.logger.info(
                        "added to history the function call (%s, %s)",
                        str(name),
                        str(result),
                    )
                # continue to generate response with the updated history
                continue

            # if there are no tool calls, return
            return response.choices[0].message.content

    def _call_function(self, function_name: str, args: dict) -> str:
        # check if the function is an internal tool
        if function_name == "clear_history":
            return self._clear_history()

        # check if the function is an external tool
        for handler in self.handlers:
            if handler.has_function(function_name):
                return handler.call_function(function_name, args)

        # if the function is not found, return an error message
        return f"Function {function_name} not found."

    def _clear_history(self) -> str:
        # clear the history, keeping only the first and last elements
        deleted_messages = max(0, len(self.history) - 2)
        self.history = list([self.history[0], self.history[-1]])
        self.logger.warning(
            "deleted chat history. Total deleted messages: %d", deleted_messages
        )
        return "History has been cleared."

    def _trim_history(self) -> None:
        if len(self.history) > OpenAIChatBot.HISTORY_LIMIT:
            self.history = [self.history[0]] + self.history[
                -1 * OpenAIChatBot.HISTORY_LIMIT :
            ]
