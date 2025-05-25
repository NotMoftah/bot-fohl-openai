from typing import Dict, List, Any, Literal, TypedDict, Optional


class FunctionDefinition(TypedDict):
    """Type definition for OpenAI function definitions."""

    type: Literal["function"]
    function: Dict[str, Any]


class ExternalFunctionsHandler:
    """
    Base class for external function handlers that can be registered with the OpenAI chat bot.
    Legacy class maintained for backward compatibility with the old system.
    """

    def __init__(self):
        """Initialize with empty functions and tools list for backward compatibility."""
        self.functions: List[FunctionDefinition] = []
        self.tools: List[FunctionDefinition] = self.functions

    def __repr__(self) -> str:
        """String representation showing registered tool names (tools or functions)."""
        # Prefer tools if set, else fallback to functions
        tool_list = getattr(self, "tools", None)
        if tool_list is None:
            tool_list = getattr(self, "functions", [])
        names = []
        for tool in tool_list:
            try:
                names.append(tool["function"]["name"])
            except Exception:
                pass
        return f"{self.__class__.__name__}({names})"

    def __str__(self) -> str:
        """String representation showing registered tool names (tools or functions)."""
        tool_list = getattr(self, "tools", None)
        if tool_list is None:
            tool_list = getattr(self, "functions", [])
        names = []
        for tool in tool_list:
            try:
                names.append(tool["function"]["name"])
            except Exception:
                pass
        return f"{self.__class__.__name__}({names})"

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
