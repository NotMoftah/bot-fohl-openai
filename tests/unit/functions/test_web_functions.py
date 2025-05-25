import sys
import os
import unittest
from unittest.mock import patch, Mock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from functions.web_functions import HttpRequestFunction


class TestHttpRequestFunction(unittest.TestCase):
    """Test the HttpRequestFunction class."""

    def setUp(self):
        """Set up test fixtures."""
        self.http_function = HttpRequestFunction()

    def test_name_property(self):
        """Test the name property."""
        self.assertEqual(self.http_function.name, "http_request")

    def test_description_property(self):
        """Test the description property."""
        self.assertEqual(
            self.http_function.description, "Send HTTP request to a specified URL."
        )

    def test_schema_property(self):
        """Test the schema property."""
        schema = self.http_function.schema
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("method", schema["properties"])
        self.assertIn("url", schema["properties"])
        self.assertIn("headers", schema["properties"])
        self.assertIn("body", schema["properties"])
        self.assertIn("required", schema)
        self.assertEqual(set(schema["required"]), {"method", "url"})
        self.assertEqual(schema["additionalProperties"], False)

    @patch("functions.web_functions.requests.get")
    def test_execute_get_request(self, mock_get):
        """Test execute method with GET request."""
        # Mock successful GET response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_get.return_value = mock_response

        # Call the function with GET method
        url = "https://example.com/api"
        headers = {"Authorization": "Bearer token123"}
        result = self.http_function.execute(method="GET", url=url, headers=headers)

        # Verify the result and that requests.get was called correctly
        self.assertIn("Response: 200", result)
        self.assertIn('{"result": "success"}', result)
        mock_get.assert_called_once_with(url, headers=headers)

    @patch("functions.web_functions.requests.post")
    def test_execute_post_request(self, mock_post):
        """Test execute method with POST request."""
        # Mock successful POST response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 42, "status": "created"}'
        mock_post.return_value = mock_response

        # Call the function with POST method
        url = "https://example.com/api/create"
        headers = {"Content-Type": "application/json"}
        body = {"name": "test", "value": 123}
        result = self.http_function.execute(
            method="POST", url=url, headers=headers, body=body
        )

        # Verify the result and that requests.post was called correctly
        self.assertIn("Response: 201", result)
        self.assertIn('{"id": 42, "status": "created"}', result)
        mock_post.assert_called_once_with(url, headers=headers, json=body)

    def test_execute_unsupported_method(self):
        """Test execute method with unsupported HTTP method."""
        result = self.http_function.execute(
            method="DELETE", url="https://example.com/api/resource/123"
        )

        # Verify the result indicates unsupported method
        self.assertIn("Unsupported HTTP method: DELETE", result)

    @patch("functions.web_functions.requests.get")
    def test_execute_get_request_exception(self, mock_get):
        """Test execute method when an exception occurs."""
        # Make requests.get raise an exception
        mock_get.side_effect = Exception("Connection error")

        # Call the function with GET method
        result = self.http_function.execute(
            method="GET", url="https://nonexistent-domain.example"
        )

        # Verify the result contains the error message
        self.assertIn("HTTP request failed:", result)
        self.assertIn("Connection error", result)

    @patch("functions.web_functions.requests.get")
    def test_execute_with_default_headers(self, mock_get):
        """Test execute with no headers specified."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_get.return_value = mock_response

        # Call the function without headers
        result = self.http_function.execute(method="GET", url="https://example.com")

        # Verify empty headers were passed
        mock_get.assert_called_once_with("https://example.com", headers={})
        self.assertIn("Response: 200", result)


if __name__ == "__main__":
    unittest.main()
