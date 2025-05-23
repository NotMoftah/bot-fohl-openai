import inspect
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Protocol, Set, Optional, Type, Callable, Union


class Tool(Protocol):
    """Protocol defining the interface for a tool."""

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        ...

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        ...

    @property
    def schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the tool."""
        ...

    def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        ...


class BaseTool(ABC):
    """Base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of the tool."""
        pass

    @property
    def schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for the tool.
        Default implementation extracts schema from execute method signature.
        """
        params = inspect.signature(self.execute).parameters
        properties = {}
        required = []

        for param_name, param in params.items():
            if param_name == "self":
                continue

            properties[param_name] = {"type": "string"}
            annotation = param.annotation

            # Handle type annotations
            if annotation != inspect.Parameter.empty:
                if annotation == str:
                    properties[param_name] = {"type": "string"}
                elif annotation == int:
                    properties[param_name] = {"type": "integer"}
                elif annotation == float:
                    properties[param_name] = {"type": "number"}
                elif annotation == bool:
                    properties[param_name] = {"type": "boolean"}
                elif annotation == Dict:
                    properties[param_name] = {"type": "object"}
                elif annotation == List:
                    properties[param_name] = {"type": "array"}

            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        pass

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert the tool to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
                "strict": True,
            },
        }


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool with the registry.

        Args:
            tool: The tool to register
        """
        if tool.name in self.tools:
            self.logger.warning(f"Tool {tool.name} already registered. Overwriting.")

        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    def register_tools(self, tools: List[Tool]) -> None:
        """
        Register multiple tools with the registry.

        Args:
            tools: The tools to register
        """
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: The name of the tool

        Returns:
            The tool, or None if not found
        """
        return self.tools.get(name)

    def get_tools_for_user(self, user_id: str) -> List[Tool]:
        """
        Get tools available for a specific user.
        Default implementation returns all tools.

        Args:
            user_id: The user ID

        Returns:
            List of available tools
        """
        return list(self.tools.values())

    def list_tool_names(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def call_tool(self, name: str, **kwargs) -> Any:
        """
        Call a tool by name with the given arguments.

        Args:
            name: The name of the tool
            **kwargs: Arguments to pass to the tool

        Returns:
            Result of the tool execution

        Raises:
            ValueError: If the tool is not found
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool {name} not found")

        self.logger.info(f"Calling tool {name} with args: {kwargs}")
        return tool.execute(**kwargs)

    def get_openai_tools(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tools in OpenAI format.

        Args:
            user_id: Optional user ID to filter tools

        Returns:
            List of tools in OpenAI format
        """
        tools = (
            self.get_tools_for_user(user_id) if user_id else list(self.tools.values())
        )

        result = []
        for tool in tools:
            if hasattr(tool, "to_openai_tool"):
                result.append(tool.to_openai_tool())
            else:
                # Create basic tool format
                result.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.schema,
                            "strict": True,
                        },
                    }
                )

        return result
