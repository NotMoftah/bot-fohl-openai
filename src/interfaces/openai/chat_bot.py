import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from core.context import UserContextManager, UserContext
from tools import ToolRegistry, LegacyToolAdapter


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

    DEFAULT_TOOLS = [
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
        tool_registry: Optional[ToolRegistry] = None,
    ):
        """
        Initialize the OpenAI chat bot.

        Args:
            api_key: OpenAI API key
            context_manager: Manager for user conversation contexts
            config: Configuration for OpenAI API calls
            tool_registry: Registry for tools that can be used by the chat bot
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = AsyncOpenAI(api_key=api_key, timeout=10)
        self.context_manager = context_manager or UserContextManager()
        self.config = config or OpenAIConfig()
        self.tool_registry = tool_registry or ToolRegistry()
        self.handlers = []
        self.tools = list(OpenAIChatBot.DEFAULT_TOOLS)

        # Add default tools to registry
        self.logger.info("OpenAIChatBot initialized.")

    def register_external_tools(self, handler) -> None:
        """
        Register external tools with the chat bot.

        This method supports both legacy ExternalToolsHandler and new Tool objects.
        For backward compatibility, it adds the handler to the handlers list.

        Args:
            handler: The tool handler to register
        """
        # Check for legacy handler
        if not hasattr(handler, "tools") or not hasattr(handler, "call_function"):
            raise TypeError(
                "Handler must have 'tools' attribute and 'call_function' method."
            )

        # For legacy handlers, keep track of them separately and add to tool registry
        if handler not in self.handlers:
            self.handlers.append(handler)
            # Add handler tools to the list for OpenAI API
            self.tools.extend(handler.tools)
            # Log the registration
            self.logger.info("Registered legacy external tools handler: %s", handler)

    def register_tool(self, tool) -> None:
        """
        Register a tool with the chat bot.

        Args:
            tool: The tool to register
        """
        try:
            self.tool_registry.register_tool(tool)
            # Update the tools list for OpenAI API
            self.tools = (
                list(OpenAIChatBot.DEFAULT_TOOLS)
                + self.tool_registry.get_openai_tools()
            )
            self.logger.info(f"Registered tool: {tool.name}")
        except Exception as e:
            self.logger.error(f"Error registering tool: {e}")
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
        # Get the user's context
        user_context = self.context_manager.get_context(user_id)

        # Add user message to history
        user_context.add_message({"role": "user", "content": message})
        self.logger.info("[User %s] Added message to history: %s", user_id, message)

        # Generate response
        response = await self._generate_response(user_id, model or self.config.model)

        # Trim history if needed
        self._trim_history(user_context)

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

        while True:
            # Make request to OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                tools=self.tools,
                messages=history_with_system,
                n=1,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_tokens=self.config.max_tokens,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
            )

            # Break if there are no choices in the response
            if len(response.choices) == 0:
                break

            # Add the assistant response to the history
            assistant_message = {
                "role": "assistant",
                "content": response.choices[0].message.content,
            }

            # Add tool_calls if present
            if response.choices[0].message.tool_calls:
                assistant_message["tool_calls"] = response.choices[0].message.tool_calls

            user_context.add_message(assistant_message)
            self.logger.info(
                "[User %s] Added assistant response: %s",
                user_id,
                response.choices[0].message.content,
            )

            # Check if there are any tool calls in the response
            tool_calls = response.choices[0].message.tool_calls
            if tool_calls is not None and len(tool_calls) > 0:
                for tool_call in response.choices[0].message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    # Handle special case for clear_history
                    if name == "clear_history":
                        result = self._clear_history(user_id)
                        # Refresh context after clearing
                        user_context = self.context_manager.get_context(user_id)
                        history_with_system = (
                            user_context.get_history_with_system_message(
                                self.config.system_message
                            )
                        )
                    else:
                        # Call external tool
                        result = self._call_function(name, args)

                    self.logger.info(
                        "[User %s] Called function %s with args %s", user_id, name, args
                    )

                    # Add function call result to history
                    user_context.add_message(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )
                    self.logger.info(
                        "[User %s] Added function result for %s: %s",
                        user_id,
                        name,
                        str(result),
                    )
                # Continue generation loop with updated history
                continue

            # If there are no tool calls, return the response
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
        # First try the new tool registry
        if function_name == "clear_history":
            # Handle clear history internally
            return self._clear_history(args.get("user_id", "unknown"))

        try:
            # Try to call the tool using the tool registry
            if self.tool_registry.get_tool(function_name):
                result = self.tool_registry.call_tool(function_name, **args)
                return str(result) if result is not None else ""
        except Exception as e:
            self.logger.error(f"Error calling tool {function_name}: {e}")

        # Fall back to legacy handlers if not found in registry
        for handler in self.handlers:
            if hasattr(handler, "has_function") and handler.has_function(function_name):
                return handler.call_function(function_name, args)

        # If the function is not found, return an error message
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
        # Re-add system message
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
            # Keep system message (if any) and the most recent messages
            if history and history[0].get("role") == "system":
                system_message = history[0]
                new_history = [system_message] + history[
                    -(self.config.history_limit - 1) :
                ]
                user_context.history = new_history
            else:
                user_context.history = history[-self.config.history_limit :]
