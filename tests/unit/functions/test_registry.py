import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from functions.registry import FunctionRegistry, BaseFunction


class TestBaseFunction(unittest.TestCase):
    """Test the BaseFunction abstract class."""

    def test_to_openai_function(self):
        """Test the to_openai_function method."""
        # Create a concrete implementation of BaseFunction
        mock_function = Mock(spec=BaseFunction)
        mock_function.name = "test_function"
        mock_function.description = "Test function description"
        mock_function.schema = {
            "type": "object",
            "properties": {"test_param": {"type": "string"}},
        }

        # Get the to_openai_function method and bind it to our mock
        to_openai_function = BaseFunction.to_openai_function.__get__(mock_function)

        # Call the method
        result = to_openai_function()

        # Verify the result
        self.assertEqual(result["type"], "function")
        self.assertEqual(result["name"], "test_function")
        self.assertEqual(result["description"], "Test function description")
        self.assertEqual(result["parameters"], mock_function.schema)
        self.assertEqual(result["strict"], True)


class MockFunction(BaseFunction):
    """Mock concrete implementation of BaseFunction for testing."""

    def __init__(self, name="mock_function", raises_error=False):
        self._name = name
        self.raises_error = raises_error
        self.called_with = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"{self._name} description"

    @property
    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Test parameter"}
            },
            "required": ["param"],
        }

    def execute(self, **kwargs):
        self.called_with = kwargs
        if self.raises_error:
            raise ValueError("Test error")
        return f"Executed {self._name} with {kwargs}"


class TestFunctionRegistry(unittest.TestCase):
    """Test the FunctionRegistry class."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = FunctionRegistry()
        self.test_function = MockFunction()

    def test_init(self):
        """Test initialization of FunctionRegistry."""
        self.assertEqual(self.registry.functions, {})

    def test_register_function(self):
        """Test registering a function."""
        self.registry.register_function(self.test_function)
        self.assertIn("mock_function", self.registry.functions)
        self.assertEqual(self.registry.functions["mock_function"], self.test_function)

    def test_register_duplicate_function(self):
        """Test registering a function with the same name twice."""
        self.registry.register_function(self.test_function)
        duplicate = MockFunction()  # Same name as self.test_function
        self.registry.register_function(duplicate)
        # Should overwrite the original
        self.assertEqual(self.registry.functions["mock_function"], duplicate)

    def test_get_function_existing(self):
        """Test getting an existing function."""
        self.registry.register_function(self.test_function)
        result = self.registry.get_function("mock_function")
        self.assertEqual(result, self.test_function)

    def test_get_function_nonexistent(self):
        """Test getting a non-existent function."""
        result = self.registry.get_function("nonexistent")
        self.assertIsNone(result)

    def test_call_function_existing(self):
        """Test calling an existing function."""
        self.registry.register_function(self.test_function)
        result = self.registry.call_function("mock_function", param="test")
        self.assertEqual(result, "Executed mock_function with {'param': 'test'}")
        self.assertEqual(self.test_function.called_with, {"param": "test"})

    def test_call_function_nonexistent(self):
        """Test calling a non-existent function."""
        with self.assertRaises(ValueError):
            self.registry.call_function("nonexistent", param="test")

    def test_call_function_error(self):
        """Test calling a function that raises an error."""
        error_function = MockFunction(raises_error=True)
        self.registry.register_function(error_function)
        with self.assertRaises(ValueError):
            self.registry.call_function("mock_function", param="test")

    def test_get_openai_functions(self):
        """Test getting functions in OpenAI format."""
        self.registry.register_function(self.test_function)

        # Add another function with a different name
        another_function = MockFunction("another_function")
        self.registry.register_function(another_function)

        result = self.registry.get_openai_functions()

        # Should return a list of function definitions
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Verify the function definitions
        functions = {func["name"]: func for func in result}
        self.assertIn("mock_function", functions)
        self.assertIn("another_function", functions)

        # Verify the details of the first function
        func = functions["mock_function"]
        self.assertEqual(func["type"], "function")
        self.assertEqual(func["description"], "mock_function description")
        self.assertTrue("parameters" in func)
        self.assertEqual(func["strict"], True)


if __name__ == "__main__":
    unittest.main()
