import sys
import os
import unittest
from unittest.mock import patch
import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from functions.time_functions import GetTimeFunction


class TestGetTimeFunction(unittest.TestCase):
    """Test the GetTimeFunction class."""

    def setUp(self):
        """Set up test fixtures."""
        self.time_function = GetTimeFunction()

    def test_name_property(self):
        """Test the name property."""
        self.assertEqual(self.time_function.name, "get_time")

    def test_description_property(self):
        """Test the description property."""
        self.assertEqual(
            self.time_function.description, "Get current time using a specified format."
        )

    def test_schema_property(self):
        """Test the schema property."""
        schema = self.time_function.schema
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("format", schema["properties"])
        self.assertIn("required", schema)
        self.assertEqual(schema["required"], ["format"])
        self.assertEqual(schema["additionalProperties"], False)

    @patch("functions.time_functions.datetime")
    def test_execute_with_default_format(self, mock_datetime):
        """Test execute method with default format."""
        # Mock datetime to return a fixed time
        mock_dt = mock_datetime.datetime
        mock_dt.now.return_value = datetime.datetime(2025, 5, 25, 16, 30, 0)

        # Set expected output based on the format string
        expected_time = "04:30PM - May 25, 2025"
        mock_dt.now().strftime.return_value = expected_time

        # Call the function with default format
        result = self.time_function.execute()

        # Verify the result contains the formatted time
        self.assertEqual(result, f"The current time is {expected_time}.")
        mock_dt.now().strftime.assert_called_once_with("%I:%M%p - %B %d, %Y")

    @patch("functions.time_functions.datetime")
    def test_execute_with_custom_format(self, mock_datetime):
        """Test execute method with custom format."""
        # Mock datetime to return a fixed time
        mock_dt = mock_datetime.datetime
        mock_dt.now.return_value = datetime.datetime(2025, 5, 25, 16, 30, 0)

        # Set expected output based on the custom format string
        custom_format = "%Y-%m-%d %H:%M:%S"
        expected_time = "2025-05-25 16:30:00"
        mock_dt.now().strftime.return_value = expected_time

        # Call the function with custom format
        result = self.time_function.execute(format=custom_format)

        # Verify the result contains the formatted time
        self.assertEqual(result, f"The current time is {expected_time}.")
        mock_dt.now().strftime.assert_called_once_with(custom_format)

    def test_to_openai_function(self):
        """Test the to_openai_function method inherited from BaseFunction."""
        result = self.time_function.to_openai_function()

        # Verify structure of the OpenAI function definition
        self.assertEqual(result["type"], "function")
        self.assertEqual(result["name"], "get_time")
        self.assertEqual(
            result["description"], "Get current time using a specified format."
        )
        self.assertEqual(result["parameters"], self.time_function.schema)
        self.assertEqual(result["strict"], True)


if __name__ == "__main__":
    unittest.main()
