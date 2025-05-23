import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from core.tool_handler import ExternalToolsHandler, FunctionTool


class MockExternalToolsHandler(ExternalToolsHandler):
    """Mock implementation of ExternalToolsHandler for testing."""
    
    def __init__(self):
        super().__init__()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_function",
                    "description": "A test function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {"type": "string", "description": "Test input"}
                        },
                        "required": ["input"]
                    }
                }
            }
        ]
    
    def has_function(self, name: str) -> bool:
        return name == "test_function"
      def call_function(self, name: str, args: dict) -> str:
        if name == "test_function":
            if args is None:
                args = {}
            return f"Test result: {args.get('input', 'no input')}"
        return "Unknown function"


class TestExternalToolsHandler(unittest.TestCase):
    def setUp(self):
        self.handler = MockExternalToolsHandler()

    def test_init(self):
        """Test ExternalToolsHandler initialization."""
        handler = ExternalToolsHandler()
        self.assertEqual(handler.tools, [])

    def test_init_with_tools(self):
        """Test initialization with predefined tools."""
        self.assertEqual(len(self.handler.tools), 1)
        self.assertEqual(self.handler.tools[0]["type"], "function")
        self.assertEqual(self.handler.tools[0]["function"]["name"], "test_function")

    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.handler)
        self.assertIn("MockExternalToolsHandler", repr_str)
        self.assertIn("test_function", repr_str)

    def test_str(self):
        """Test string conversion."""
        str_repr = str(self.handler)
        self.assertIn("MockExternalToolsHandler", str_repr)
        self.assertIn("test_function", str_repr)

    def test_repr_empty_tools(self):
        """Test string representation with empty tools."""
        handler = ExternalToolsHandler()
        repr_str = repr(handler)
        self.assertIn("ExternalToolsHandler", repr_str)
        self.assertIn("[]", repr_str)

    def test_has_function_existing(self):
        """Test has_function with existing function."""
        self.assertTrue(self.handler.has_function("test_function"))

    def test_has_function_nonexistent(self):
        """Test has_function with non-existent function."""
        self.assertFalse(self.handler.has_function("nonexistent_function"))

    def test_call_function_existing(self):
        """Test calling an existing function."""
        result = self.handler.call_function("test_function", {"input": "hello"})
        self.assertEqual(result, "Test result: hello")

    def test_call_function_no_input(self):
        """Test calling function with no input."""
        result = self.handler.call_function("test_function", {})
        self.assertEqual(result, "Test result: no input")

    def test_call_function_nonexistent(self):
        """Test calling a non-existent function."""
        result = self.handler.call_function("nonexistent_function", {})
        self.assertEqual(result, "Unknown function")

    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods raise NotImplementedError."""
        handler = ExternalToolsHandler()
        
        with self.assertRaises(NotImplementedError):
            handler.has_function("test")
        
        with self.assertRaises(NotImplementedError):
            handler.call_function("test", {})

    def test_multiple_tools(self):
        """Test handler with multiple tools."""
        class MultiToolHandler(ExternalToolsHandler):
            def __init__(self):
                super().__init__()
                self.tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "function1",
                            "description": "First function"
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "function2",
                            "description": "Second function"
                        }
                    }
                ]
            
            def has_function(self, name: str) -> bool:
                return name in ["function1", "function2"]
            
            def call_function(self, name: str, args: dict) -> str:
                return f"Called {name}"
        
        handler = MultiToolHandler()
        repr_str = repr(handler)
        self.assertIn("function1", repr_str)
        self.assertIn("function2", repr_str)
        
        self.assertTrue(handler.has_function("function1"))
        self.assertTrue(handler.has_function("function2"))
        self.assertFalse(handler.has_function("function3"))

    def test_function_tool_type(self):
        """Test FunctionTool type structure."""
        tool: FunctionTool = {
            "type": "function",
            "function": {
                "name": "test",
                "description": "test function",
                "parameters": {"type": "object"}
            }
        }
        
        self.assertEqual(tool["type"], "function")
        self.assertIn("name", tool["function"])
        self.assertIn("description", tool["function"])
        self.assertIn("parameters", tool["function"])

    def test_complex_function_parameters(self):
        """Test handler with complex function parameters."""
        class ComplexHandler(ExternalToolsHandler):
            def __init__(self):
                super().__init__()
                self.tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "complex_function",
                            "description": "A complex function with multiple parameters",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "number": {"type": "integer"},
                                    "flag": {"type": "boolean"},
                                    "items": {"type": "array", "items": {"type": "string"}},
                                    "config": {"type": "object"}
                                },
                                "required": ["text", "number"],
                                "additionalProperties": False
                            },
                            "strict": True
                        }
                    }
                ]
            
            def has_function(self, name: str) -> bool:
                return name == "complex_function"
            
            def call_function(self, name: str, args: dict) -> str:
                if name == "complex_function":
                    return f"Complex result: {args}"
                return "Unknown function"
        
        handler = ComplexHandler()
        tool = handler.tools[0]
        
        # Verify structure
        self.assertEqual(tool["function"]["name"], "complex_function")
        self.assertIn("properties", tool["function"]["parameters"])
        self.assertEqual(len(tool["function"]["parameters"]["properties"]), 5)
        self.assertEqual(tool["function"]["parameters"]["required"], ["text", "number"])
        
        # Test function call
        args = {
            "text": "hello",
            "number": 42,
            "flag": True,
            "items": ["a", "b", "c"],
            "config": {"key": "value"}
        }
        result = handler.call_function("complex_function", args)
        self.assertIn("Complex result:", result)

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with None args
        result = self.handler.call_function("test_function", None)
        # Should handle gracefully (implementation dependent)
        self.assertIsInstance(result, str)
        
        # Test with empty string function name
        self.assertFalse(self.handler.has_function(""))
        
        # Test with special characters in function name
        self.assertFalse(self.handler.has_function("test@function"))


if __name__ == "__main__":
    unittest.main()
