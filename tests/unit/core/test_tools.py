import unittest

from unittest.mock import patch, MagicMock
from utils.tools import TimeTools, WebTools


class TestTimeTools(unittest.TestCase):
    def setUp(self):
        self.time_tools = TimeTools()

    def test_has_function(self):
        self.assertTrue(self.time_tools.has_function("get_time"))
        self.assertFalse(self.time_tools.has_function("invalid_function"))

    @patch("utils.tools.datetime")
    def test_get_time(self, mock_datetime):
        # Mock datetime.now() to return a specific time
        mock_now = MagicMock()
        mock_datetime.datetime.now.return_value = mock_now
        mock_now.strftime.return_value = "10:30AM - January 01, 2023"

        # Test with default format
        result = self.time_tools.call_function(
            "get_time", {"format": "%I:%M%p - %B %d, %Y"}
        )
        self.assertEqual(result, "The current time is 10:30AM - January 01, 2023.")

        # Test with custom format
        result = self.time_tools.call_function("get_time", {"format": "%H:%M"})
        mock_now.strftime.assert_called_with("%H:%M")


class TestWebTools(unittest.TestCase):
    def setUp(self):
        self.web_tools = WebTools()

    def test_has_function(self):
        self.assertTrue(self.web_tools.has_function("http_request"))
        self.assertFalse(self.web_tools.has_function("invalid_function"))

    @patch("utils.tools.requests.get")
    def test_http_get_request(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "test"}'
        mock_get.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "GET",
                "url": "https://example.com",
                "headers": {"Content-Type": "application/json"},
            },
        )

        self.assertIn("Response: 200", result)
        self.assertIn('{"data": "test"}', result)
        mock_get.assert_called_once_with(
            "https://example.com", headers={"Content-Type": "application/json"}
        )

    @patch("utils.tools.requests.post")
    def test_http_post_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"status": "created"}'
        mock_post.return_value = mock_response

        result = self.web_tools.call_function(
            "http_request",
            {
                "method": "POST",
                "url": "https://example.com/create",
                "headers": {"Content-Type": "application/json"},
                "body": {"name": "test"},
            },
        )

        self.assertIn("Response: 201", result)
        self.assertIn('{"status": "created"}', result)
        mock_post.assert_called_once_with(
            "https://example.com/create",
            headers={"Content-Type": "application/json"},
            json={"name": "test"},
        )

    def test_unsupported_http_method(self):
        result = self.web_tools.call_function(
            "http_request",
            {"method": "PUT", "url": "https://example.com", "headers": {}, "body": {}},
        )
        self.assertIn("Unsupported HTTP method", result)


if __name__ == "__main__":
    unittest.main()
