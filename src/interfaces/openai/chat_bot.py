import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from core.context import UserContextManager, UserContext
from functions import FunctionRegistry


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API calls."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.8
    top_p: float = 0.8
    max_tokens: int = 256
    frequency_penalty: float = 0
    presence_penalty: float = 0
    history_limit: int = 20
    system_message: str = (
        "You are a helpful assistant that always responds in raw text format."
    )


class OpenAIChatBot:
    """
    A chat bot that uses OpenAI's API to generate responses.
    Maintains separate conversation history for each user.
    """

    DEFAULT_FUNCTIONS = [
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

    def __init__(
        self,
        api_key: str,
        context_manager: Optional[UserContextManager] = None,
        config: Optional[OpenAIConfig] = None,
        function_registry: Optional[FunctionRegistry] = None,
    ):
        """
        Initialize the OpenAI chat bot.

        Args:
            api_key: OpenAI API key
            context_manager: Manager for user conversation contexts
            config: Configuration for OpenAI API calls
            function_registry: Registry for functions that can be used by the chat bot
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.client = AsyncOpenAI(api_key=api_key, timeout=10)
        self.context_manager = context_manager or UserContextManager()
        self.config = config or OpenAIConfig()
        self.function_registry = function_registry or FunctionRegistry()
        self.handlers = []
        self.functions = (
            list(OpenAIChatBot.DEFAULT_FUNCTIONS)
            + self.function_registry.get_openai_functions()
        )
        self.logger.info(
            "OpenAIChatBot initialized with model: %s, functions: %s",
            self.config.model,
            self.functions,
        )

    def register_external_functions(self, handler) -> None:
        """
        Register external functions with the chat bot.

        This method supports both legacy ExternalFunctionsHandler and new Function objects.
        For backward compatibility, it adds the handler to the handlers list.

        Args:
            handler: The function handler to register
        """
        # Check for legacy handler
        if not hasattr(handler, "functions") or not hasattr(handler, "call_function"):
            raise TypeError(
                "Handler must have 'functions' attribute and 'call_function' method."
            )

        # For legacy handlers, keep track of them separately and add to function registry
        if handler not in self.handlers:
            self.handlers.append(handler)
            self.functions.extend(handler.functions)
            self.logger.info(
                "Registered legacy external functions handler: %s, functions: %s",
                handler,
                [f["function"]["name"] for f in handler.functions],
            )

    def register_function(self, function) -> None:
        """
        Register a function with the chat bot.

        Args:
            function: The function to register
        """
        try:
            self.function_registry.register_function(function)
            self.functions = (
                list(OpenAIChatBot.DEFAULT_FUNCTIONS)
                + self.function_registry.get_openai_functions()
            )
            self.logger.info(f"Registered function: {function.name}.")
        except Exception as e:
            self.logger.error(f"Error registering function: {e}", exc_info=True)
            raise

    async def send_message(
        self, user_id: str, message: str, model: Optional[str] = None
    ) -> str:
        """
        Send a message to the chat bot and get a response.

        Args:
            user_id: Unique identifier for the user
            message: Message from the user
            model: Optional model override

        Returns:
            Response from the chat bot
        """
        self.logger.info("[User %s] Incoming message: %s", user_id, message)
        user_context = self.context_manager.get_context(user_id)
        user_context.add_message({"role": "user", "content": message})
        self.logger.info(
            "[User %s] Added message to history. Current history length: %d",
            user_id,
            len(user_context.get_history()),
        )
        try:
            response = await self._generate_response(
                user_id, model or self.config.model
            )
        except Exception as e:
            self.logger.error(
                "[User %s] Error during response generation: %s",
                user_id,
                e,
                exc_info=True,
            )
            raise
        self._trim_history(user_context)
        self.logger.info(
            "[User %s] History trimmed. Current length: %d",
            user_id,
            len(user_context.get_history()),
        )
        return response

    async def _generate_response(self, user_id: str, model: str) -> str:
        """
        Generate a response to the user's message.

        Args:
            user_id: Unique identifier for the user
            model: Model to use for generation

        Returns:
            Response from the chat bot
        """
        user_context = self.context_manager.get_context(user_id)
        history_with_system = user_context.get_history_with_system_message(
            self.config.system_message
        )
        self.logger.info("[User %s] Generating response with model: %s", user_id, model)
        while True:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    tools=self.functions,
                    messages=history_with_system,
                    n=1,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens,
                    frequency_penalty=self.config.frequency_penalty,
                    presence_penalty=self.config.presence_penalty,
                )
            except Exception as e:
                self.logger.error(
                    "[User %s] OpenAI API call failed: %s", user_id, e, exc_info=True
                )
                raise
            if len(response.choices) == 0:
                self.logger.warning(
                    "[User %s] No choices returned from OpenAI API", user_id
                )
                break
            assistant_message = {
                "role": "assistant",
                "content": response.choices[0].message.content,
            }
            if response.choices[0].message.tool_calls:
                assistant_message["tool_calls"] = response.choices[0].message.tool_calls
            user_context.add_message(assistant_message)
            self.logger.info(
                "[User %s] Assistant response: %s",
                user_id,
                response.choices[0].message.content,
            )
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls is not None and len(tool_calls) > 0:
                for tool_call in tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    self.logger.info(
                        "[User %s] Function call requested: %s with args %s",
                        user_id,
                        name,
                        args,
                    )
                    if name == "clear_history":
                        result = self._clear_history(user_id)
                        user_context = self.context_manager.get_context(user_id)
                        history_with_system = (
                            user_context.get_history_with_system_message(
                                self.config.system_message
                            )
                        )
                    else:
                        result = self._call_function(name, args)
                    self.logger.info(
                        "[User %s] Function call result for %s: %s",
                        user_id,
                        name,
                        result,
                    )
                    user_context.add_message(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )
                continue
            return response.choices[0].message.content

    def _call_function(self, function_name: str, args: dict) -> str:
        """
        Call a function by name with the given arguments.

        Args:
            function_name: Name of the function to call
            args: Arguments to pass to the function

        Returns:
            Result of the function call
        """
        self.logger.info("Calling function: %s with args: %s", function_name, args)
        if function_name == "clear_history":
            return self._clear_history(args.get("user_id", "unknown"))
        try:
            if self.function_registry.get_function(function_name):
                result = self.function_registry.call_function(function_name, **args)
                self.logger.info(
                    "Function %s executed via FunctionRegistry. Result: %s",
                    function_name,
                    result,
                )
                return str(result) if result is not None else ""
        except Exception as e:
            self.logger.error(
                "Error calling function %s: %s", function_name, e, exc_info=True
            )
        for handler in self.handlers:
            if hasattr(handler, "has_function") and handler.has_function(function_name):
                self.logger.info(
                    "Function %s executed via legacy handler %s", function_name, handler
                )
                return handler.call_function(function_name, args)
        self.logger.warning(
            "Function %s not found in any registry or handler", function_name
        )
        return f"Function {function_name} not found."

    def _clear_history(self, user_id: str) -> str:
        """
        Clear the conversation history for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Confirmation message
        """
        user_context = self.context_manager.get_context(user_id)
        user_context.clear_history()
        self.logger.warning("[User %s] Cleared chat history", user_id)
        user_context.add_system_message(self.config.system_message)
        return "History has been cleared."

    def _trim_history(self, user_context: UserContext) -> None:
        """
        Trim the conversation history if it exceeds the limit.

        Args:
            user_context: User's conversation context
        """
        history = user_context.get_history()
        if len(history) > self.config.history_limit:
            if history and history[0].get("role") == "system":
                system_message = history[0]
                new_history = [system_message] + history[
                    -(self.config.history_limit - 1) :
                ]
                user_context.history = new_history
            else:
                user_context.history = history[-self.config.history_limit :]
        self.logger.info(
            "Trimmed user history to %d messages", len(user_context.get_history())
        )
