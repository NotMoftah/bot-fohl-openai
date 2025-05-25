import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Protocol, Set, Optional, Type, Callable, Union


class Function(Protocol):
    """Protocol defining the interface for an LLM function."""

    @property
    def name(self) -> str:
        """Get the name of the function."""
        ...

    @property
    def description(self) -> str:
        """Get the description of the function."""
        ...

    @property
    def schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the function."""
        ...

    def execute(self, **kwargs) -> Any:
        """Execute the function with the given arguments."""
        ...


class BaseFunction(ABC):
    """Base class for LLM functions."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the function."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of the function."""
        pass

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for the function.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the function with the given arguments."""
        pass

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert the function to OpenAI function format."""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.schema,
            "strict": True,
        }


class FunctionRegistry:
    """Registry for managing functions."""

    def __init__(self):
        self.functions: Dict[str, Function] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def register_function(self, function: Function) -> None:
        """
        Register a function with the registry.

        Args:
            function: The function to register
        """
        if function.name in self.functions:
            self.logger.warning(
                f"Function {function.name} already registered. Overwriting."
            )

        self.functions[function.name] = function
        self.logger.info(f"Registered Function: {function.name}")

    def get_function(self, name: str) -> Optional[Function]:
        """
        Get a function by name.

        Args:
            name: The name of the function

        Returns:
            The function, or None if not found
        """
        return self.functions.get(name)

    def call_function(self, name: str, **kwargs) -> Any:
        """
        Call a function by name with the given arguments.

        Args:
            name: The name of the function
            **kwargs: Arguments to pass to the function

        Returns:
            Result of the function execution

        Raises:
            ValueError: If the function is not found
        """
        function = self.get_function(name)
        if function is None:
            self.logger.error(f"Function {name} not found")
            raise ValueError(f"Function {name} not found")

        self.logger.info(f"Calling function {name} with args: {kwargs}")
        return function.execute(**kwargs)

    def get_openai_functions(
        self, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get functions in OpenAI format.

        Args:
            user_id: Optional user ID to filter functions

        Returns:
            List of functions in OpenAI format
        """
        result = []
        for function in self.functions.values():
            if hasattr(function, "to_openai_function"):
                result.append(function.to_openai_function())

        return result
