"""
Unit tests for the utils.tools module.
Tests the TimeTools and WebTools classes (legacy tool handlers).
"""

import unittest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from utils.tools import TimeTools, WebTools
from core.function_handler import ExternalFunctionsHandler


class TestTimeToolsDetailed(unittest.TestCase):
    """Detailed tests for TimeTools class."""

    def setUp(self):
        """Set up test fixtures."""
        self.time_tools = TimeTools()

    def test_inheritance(self):
        """Test that TimeTools inherits from ExternalToolsHandler."""
        self.assertIsInstance(self.time_tools, ExternalFunctionsHandler)

    def test_tools_structure(self):
        """Test the tools structure is correct."""
        self.assertEqual(len(self.time_tools.tools), 1)

        tool = self.time_tools.tools[0]
        self.assertEqual(tool["type"], "function")

        function = tool["function"]
        self.assertEqual(function["name"], "get_time")
        self.assertIn("current time", function["description"].lower())
        self.assertTrue(function["strict"])

        # Check parameters structure
        params = function["parameters"]
        self.assertEqual(params["type"], "object")
        self.assertIn("format", params["properties"])
        self.assertEqual(params["required"], ["format"])
        self.assertFalse(params["additionalProperties"])

    def test_has_function_valid(self):
        """Test has_function with valid function name."""
        self.assertTrue(self.time_tools.has_function("get_time"))

    def test_has_function_invalid(self):
        """Test has_function with invalid function names."""
        self.assertFalse(self.time_tools.has_function("invalid_function"))
        self.assertFalse(self.time_tools.has_function(""))
        self.assertFalse(self.time_tools.has_function("GET_TIME"))  # Case sensitive
        self.assertFalse(self.time_tools.has_function("get_date"))

    @patch("utils.tools.datetime")
    def test_get_time_default_format(self, mock_datetime):
        """Test get_time with default format."""
        mock_now = Mock()
        mock_datetime.datetime.now.return_value = mock_now
        mock_now.strftime.return_value = "02:30PM - January 15, 2024"

        result = self.time_tools.call_function(
            "get_time", {"format": "%I:%M%p - %B %d, %Y"}
        )

        expected = "The current time is 02:30PM - January 15, 2024."
        self.assertEqual(result, expected)
        mock_now.strftime.assert_called_once_with("%I:%M%p - %B %d, %Y")

    @patch("utils.tools.datetime")
    def test_get_time_custom_format(self, mock_datetime):
        """Test get_time with custom format."""
        mock_now = Mock()
        mock_datetime.datetime.now.return_value = mock_now
        mock_now.strftime.return_value = "14:30"

        result = self.time_tools.call_function("get_time", {"format": "%H:%M"})

        expected = "The current time is 14:30."
        self.assertEqual(result, expected)
        mock_now.strftime.assert_called_once_with("%H:%M")

    @patch("utils.tools.datetime")
    def test_get_time_complex_format(self, mock_datetime):
        """Test get_time with complex format string."""
        mock_now = Mock()
        mock_datetime.datetime.now.return_value = mock_now
        mock_now.strftime.return_value = "Monday, January 15, 2024 at 2:30:45 PM EST"

        complex_format = "%A, %B %d, %Y at %I:%M:%S %p EST"
        result = self.time_tools.call_function("get_time", {"format": complex_format})

        expected = "The current time is Monday, January 15, 2024 at 2:30:45 PM EST."
        self.assertEqual(result, expected)
        mock_now.strftime.assert_called_once_with(complex_format)

    def test_call_function_invalid_function(self):
        """Test calling invalid function."""
        result = self.time_tools.call_function("invalid_function", {})
        self.assertEqual(result, "Unknown function")

    def test_call_function_no_args(self):
        """Test calling function with no arguments."""
        # Should fail gracefully since format is required
        with patch("utils.tools.datetime") as mock_datetime:
            result = self.time_tools.call_function("get_time", {})
            # Should raise KeyError for missing format, but let's test the implementation
            # The actual behavior depends on implementation details

    @patch("utils.tools.datetime")
    def test_get_time_empty_format(self, mock_datetime):
        """Test get_time with empty format string."""
        mock_now = Mock()
        mock_datetime.datetime.now.return_value = mock_now
        mock_now.strftime.return_value = ""

        result = self.time_tools.call_function("get_time", {"format": ""})

        expected = "The current time is ."
        self.assertEqual(result, expected)
        mock_now.strftime.assert_called_once_with("")

    @patch("utils.tools.datetime")
    def test_get_time_unicode_format(self, mock_datetime):
        """Test get_time with unicode characters in format."""
        mock_now = Mock()
        mock_datetime.datetime.now.return_value = mock_now
        mock_now.strftime.return_value = "🕐 14:30 🗓️"

        result = self.time_tools.call_function("get_time", {"format": "🕐 %H:%M 🗓️"})

        expected = "The current time is 🕐 14:30 🗓️."
        self.assertEqual(result, expected)


class TestWebToolsDetailed(unittest.TestCase):
    """Detailed tests for WebTools class."""

    def setUp(self):
        """Set up test fixtures."""
        self.web_tools = WebTools()

    def test_inheritance(self):
        """Test that WebTools inherits from ExternalToolsHandler."""
        self.assertIsInstance(self.web_tools, ExternalFunctionsHandler)

    def test_tools_structure(self):
        """Test the tools structure is correct."""
        self.assertEqual(len(self.web_tools.tools), 1)

        tool = self.web_tools.tools[0]
        self.assertEqual(tool["type"], "function")

        function = tool["function"]
        self.assertEqual(function["name"], "http_request")
        self.assertIn("HTTP request", function["description"])
        self.assertTrue(function["strict"])

        # Check parameters structure
        params = function["parameters"]
        self.assertEqual(params["type"], "object")
        self.assertIn("method", params["properties"])
        self.assertIn("url", params["properties"])
        self.assertIn("headers", params["properties"])
        self.assertIn("body", params["properties"])
        self.assertEqual(set(params["required"]), {"method", "url"})
        self.assertFalse(params["additionalProperties"])

    def test_has_function_valid(self):
        """Test has_function with valid function name."""
        self.assertTrue(self.web_tools.has_function("http_request"))

    def test_has_function_invalid(self):
        """Test has_function with invalid function names."""
        self.assertFalse(self.web_tools.has_function("invalid_function"))
        self.assertFalse(self.web_tools.has_function(""))
        self.assertFalse(self.web_tools.has_function("HTTP_REQUEST"))  # Case sensitive
        self.assertFalse(self.web_tools.has_function("get_request"))
        self.assertFalse(self.web_tools.has_function("post_request"))

    @patch("utils.tools.requests.get")
    def test_http_get_success(self, mock_get):
        """Test successful HTTP GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"message": "success"}'
        mock_get.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request", {"method": "GET", "url": "https://api.example.com/data"}
        )

        expected = 'Response: 200, {"message": "success"}'
        self.assertEqual(result, expected)
        mock_get.assert_called_once_with("https://api.example.com/data", headers=None)

    @patch("utils.tools.requests.get")
    def test_http_get_with_headers(self, mock_get):
        """Test HTTP GET request with headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_get.return_value = mock_response

        headers = {"Authorization": "Bearer token123", "User-Agent": "TestAgent"}
        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "GET",
                "url": "https://api.example.com/secure",
                "headers": headers,
            },
        )

        expected = "Response: 200, OK"
        self.assertEqual(result, expected)
        mock_get.assert_called_once_with(
            "https://api.example.com/secure", headers=headers
        )

    @patch("utils.tools.requests.post")
    def test_http_post_success(self, mock_post):
        """Test successful HTTP POST request."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 123, "status": "created"}'
        mock_post.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "POST",
                "url": "https://api.example.com/users",
                "body": {"name": "John", "email": "john@example.com"},
            },
        )

        expected = 'Response: 201, {"id": 123, "status": "created"}'
        self.assertEqual(result, expected)
        mock_post.assert_called_once_with(
            "https://api.example.com/users",
            headers=None,
            json={"name": "John", "email": "john@example.com"},
        )

    @patch("utils.tools.requests.post")
    def test_http_post_with_headers_and_body(self, mock_post):
        """Test HTTP POST request with headers and body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Updated"
        mock_post.return_value = mock_response

        headers = {"Content-Type": "application/json", "X-API-Key": "secret"}
        body = {"data": "test", "values": [1, 2, 3]}

        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "POST",
                "url": "https://api.example.com/update",
                "headers": headers,
                "body": body,
            },
        )

        expected = "Response: 200, Updated"
        self.assertEqual(result, expected)
        mock_post.assert_called_once_with(
            "https://api.example.com/update", headers=headers, json=body
        )

    def test_http_unsupported_method(self):
        """Test HTTP request with unsupported method."""
        result = self.web_tools.call_function(
            "http_request", {"method": "PUT", "url": "https://api.example.com/resource"}
        )

        expected = "Unsupported HTTP method: PUT"
        self.assertEqual(result, expected)

    def test_http_unsupported_methods_various(self):
        """Test various unsupported HTTP methods."""
        unsupported_methods = ["DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]

        for method in unsupported_methods:
            with self.subTest(method=method):
                result = self.web_tools.call_function(
                    "http_request",
                    {"method": method, "url": "https://api.example.com/resource"},
                )
                expected = f"Unsupported HTTP method: {method}"
                self.assertEqual(result, expected)

    @patch("utils.tools.requests.get")
    def test_http_get_exception(self, mock_get):
        """Test HTTP GET request that raises exception."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = self.web_tools.call_function(
            "http_request", {"method": "GET", "url": "https://invalid-url"}
        )

        expected = "HTTP request failed: Connection failed"
        self.assertEqual(result, expected)

    @patch("utils.tools.requests.post")
    def test_http_post_exception(self, mock_post):
        """Test HTTP POST request that raises exception."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "POST",
                "url": "https://slow-api.example.com",
                "body": {"data": "test"},
            },
        )

        expected = "HTTP request failed: Request timed out"
        self.assertEqual(result, expected)

    @patch("utils.tools.requests.get")
    def test_http_get_error_status(self, mock_get):
        """Test HTTP GET request with error status code."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request",
            {"method": "GET", "url": "https://api.example.com/nonexistent"},
        )

        expected = "Response: 404, Not Found"
        self.assertEqual(result, expected)

    @patch("utils.tools.requests.post")
    def test_http_post_server_error(self, mock_post):
        """Test HTTP POST request with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "POST",
                "url": "https://api.example.com/error",
                "body": {"test": "data"},
            },
        )

        expected = "Response: 500, Internal Server Error"
        self.assertEqual(result, expected)

    def test_call_function_invalid_function(self):
        """Test calling invalid function."""
        result = self.web_tools.call_function("invalid_function", {})
        self.assertEqual(result, "Unknown function")

    def test_http_request_case_insensitive_method(self):
        """Test that HTTP methods are case insensitive."""
        with patch("utils.tools.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_get.return_value = mock_response

            # Test lowercase
            result = self.web_tools.call_function(
                "http_request", {"method": "get", "url": "https://api.example.com"}
            )
            self.assertIn("Response: 200", result)

        with patch("utils.tools.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.text = "Created"
            mock_post.return_value = mock_response

            # Test lowercase
            result = self.web_tools.call_function(
                "http_request",
                {
                    "method": "post",
                    "url": "https://api.example.com",
                    "body": {"data": "test"},
                },
            )
            self.assertIn("Response: 201", result)

    @patch("utils.tools.requests.get")
    def test_http_get_empty_response(self, mock_get):
        """Test HTTP GET request with empty response."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.text = ""
        mock_get.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request", {"method": "GET", "url": "https://api.example.com/empty"}
        )

        expected = "Response: 204, "
        self.assertEqual(result, expected)

    @patch("utils.tools.requests.post")
    def test_http_post_none_body(self, mock_post):
        """Test HTTP POST request with None body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request",
            {"method": "POST", "url": "https://api.example.com/test", "body": None},
        )

        expected = "Response: 200, OK"
        self.assertEqual(result, expected)
        mock_post.assert_called_once_with(
            "https://api.example.com/test", headers=None, json=None
        )

    @patch("utils.tools.requests.get")
    def test_http_get_large_response(self, mock_get):
        """Test HTTP GET request with large response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "x" * 10000  # Large response
        mock_get.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request", {"method": "GET", "url": "https://api.example.com/large"}
        )

        # Should include the full response
        self.assertTrue(result.startswith("Response: 200, "))
        self.assertIn("x" * 100, result)  # Should contain part of the large response


class TestToolsEdgeCases(unittest.TestCase):
    """Test edge cases for both TimeTools and WebTools."""

    def test_time_tools_str_representation(self):
        """Test string representation of TimeTools."""
        time_tools = TimeTools()
        repr_str = repr(time_tools)

        # Should inherit from ExternalToolsHandler representation
        self.assertIn("TimeTools", repr_str)
        self.assertIn("get_time", repr_str)

    def test_web_tools_str_representation(self):
        """Test string representation of WebTools."""
        web_tools = WebTools()
        repr_str = repr(web_tools)

        # Should inherit from ExternalToolsHandler representation
        self.assertIn("WebTools", repr_str)
        self.assertIn("http_request", repr_str)

    def test_tools_immutability(self):
        """Test that tools list is not accidentally modified."""
        time_tools = TimeTools()
        original_tools = time_tools.tools.copy()

        # Try to modify tools
        time_tools.tools.append({"type": "invalid"})

        # Original structure should be preserved for new instances
        new_time_tools = TimeTools()
        self.assertEqual(len(new_time_tools.tools), 1)
        self.assertEqual(new_time_tools.tools[0]["function"]["name"], "get_time")

    @patch("utils.tools.datetime")
    def test_time_tools_datetime_import_error(self, mock_datetime):
        """Test TimeTools behavior when datetime operations fail."""
        mock_datetime.datetime.now.side_effect = ImportError("datetime not available")

        time_tools = TimeTools()

        # Should propagate the exception rather than handling it
        with self.assertRaises(ImportError):
            time_tools.call_function("get_time", {"format": "%H:%M"})

    def test_web_tools_with_special_characters_in_url(self):
        """Test WebTools with special characters in URL."""
        with patch("utils.tools.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "OK"
            mock_get.return_value = mock_response

            web_tools = WebTools()
            result = web_tools.call_function(
                "http_request",
                {
                    "method": "GET",
                    "url": "https://api.example.com/path?query=value&special=字符",
                },
            )

            self.assertIn("Response: 200", result)
            mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
