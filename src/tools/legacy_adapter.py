from typing import Dict, Any, List
from core.tool_handler import ExternalToolsHandler
from .registry import ToolRegistry, Tool


class LegacyToolAdapter:
    """
    Adapter to convert between the new Tool Registry and the old ExternalToolsHandler.
    This enables backward compatibility with existing code.
    """

    @staticmethod
    def adapt_to_legacy(tool_registry: ToolRegistry) -> ExternalToolsHandler:
        """
        Create a legacy ExternalToolsHandler from a ToolRegistry.

        Args:
            tool_registry: The new tool registry

        Returns:
            A legacy ExternalToolsHandler
        """
        return ToolRegistryAdapter(tool_registry)


class ToolRegistryAdapter(ExternalToolsHandler):
    """
    Adapter that implements ExternalToolsHandler using a ToolRegistry.
    """

    def __init__(self, registry: ToolRegistry):
        """
        Create an adapter for a ToolRegistry.

        Args:
            registry: The tool registry to adapt
        """
        super().__init__()
        self.registry = registry
        # Convert the tools to legacy format
        self.tools = registry.get_openai_tools()

    def has_function(self, name: str) -> bool:
        """
        Check if the registry has a tool with the given name.

        Args:
            name: The name of the tool

        Returns:
            True if the tool exists, False otherwise
        """
        return self.registry.get_tool(name) is not None

    def call_function(self, name: str, args: Dict[str, Any]) -> str:
        """
        Call a tool by name with the given arguments.

        Args:
            name: The name of the tool
            args: Arguments to pass to the tool

        Returns:
            Result of the tool execution
        """
        try:
            result = self.registry.call_tool(name, **args)
            return str(result) if result is not None else ""
        except Exception as e:
            return f"Error calling function {name}: {str(e)}"


class LegacyToolHandler(ExternalToolsHandler):
    """
    Adapter to convert a legacy ExternalToolsHandler to a Tool that can be registered with ToolRegistry.
    """

    def __init__(self, handler: ExternalToolsHandler):
        """
        Create an adapter for a legacy tool handler.

        Args:
            handler: The legacy tool handler
        """
        super().__init__()
        self.handler = handler
        self.tools = handler.tools

    def has_function(self, name: str) -> bool:
        """
        Check if the handler has a function with the given name.

        Args:
            name: The name of the function

        Returns:
            True if the function exists, False otherwise
        """
        return self.handler.has_function(name)

    def call_function(self, name: str, args: Dict[str, Any]) -> str:
        """
        Call a function by name with the given arguments.

        Args:
            name: The name of the function
            args: Arguments to pass to the function

        Returns:
            Result of the function call
        """
        return self.handler.call_function(name, args)
