import requests
from typing import Dict, Any, Optional
from .registry import BaseFunction


class HttpRequestFunction(BaseFunction):
    """Tool to make HTTP requests."""

    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return "Send HTTP request to a specified URL."

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "HTTP method: GET or POST.",
                    "enum": ["GET", "POST"],
                },
                "url": {"type": "string", "description": "URL to send the request to."},
                "headers": {
                    "type": "object",
                    "description": "HTTP headers for the request.",
                },
                "body": {
                    "type": "object",
                    "description": "Body data for POST requests. Optional for GET requests.",
                },
            },
            "required": ["method", "url"],
            "additionalProperties": False,
        }

    def execute(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send an HTTP request to a specified URL.

        Args:
            method: HTTP method (GET or POST)
            url: URL to send the request to
            headers: Optional HTTP headers
            body: Optional body data for POST requests

        Returns:
            HTTP response as a string
        """
        try:
            headers = headers or {}

            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=body)
            else:
                return f"Unsupported HTTP method: {method}"

            return f"Response: {response.status_code}, {response.text[:1000]}"
        except Exception as e:
            return f"HTTP request failed: {str(e)}"
