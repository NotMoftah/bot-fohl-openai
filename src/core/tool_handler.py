from typing import Dict, List, Any, Literal, TypedDict, Optional


class FunctionTool(TypedDict):
    """Type definition for OpenAI function tools."""

    type: Literal["function"]
    function: Dict[str, Any]


class ExternalToolsHandler:
    """
    Base class for external tool handlers that can be registered with the OpenAI chat bot.
    Legacy class maintained for backward compatibility with the old system.
    """

    def __init__(self):
        """Initialize with empty tools list."""
        self.tools: List[FunctionTool] = []

    def __repr__(self) -> str:
        """String representation showing registered function names."""
        functions = [tool["function"]["name"] for tool in self.tools]
        return f"{self.__class__.__name__}({functions})"

    def __str__(self) -> str:
        """String representation showing registered function names."""
        functions = [tool["function"]["name"] for tool in self.tools]
        return f"{self.__class__.__name__}({functions})"

    def has_function(self, name: str) -> bool:
        """
        Check if the handler has a function with the given name.

        Args:
            name: Name of the function to check

        Returns:
            True if the function exists, False otherwise
        """
        raise NotImplementedError("Subclasses must implement has_function")

    def call_function(self, name: str, args: Dict[str, Any]) -> str:
        """
        Call a function by name with the given arguments.

        Args:
            name: Name of the function to call
            args: Arguments to pass to the function

        Returns:
            Result of the function call
        """
        raise NotImplementedError("Subclasses must implement call_function")
