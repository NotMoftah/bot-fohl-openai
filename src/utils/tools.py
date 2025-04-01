import datetime
import requests

from core import ExternalToolsHandler, FunctionTool
from typing import Dict, List, Any, Optional, Literal, TypedDict


class TimeTools(ExternalToolsHandler):
    def __init__(self) -> None:
        self.tools: List[FunctionTool] = [
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get current time using a specified format.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "description": "Python format string for the time.",
                            }
                        },
                        "required": ["format"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
        ]

    def has_function(self, name: str) -> bool:
        return name in ["get_time"]

    def call_function(self, name: str, args: Dict[str, Any]) -> str:
        if name == "get_time":
            return self._get_time(**args)
        return "Unknown function"

    def _get_time(self, format: str = "%I:%M%p - %B %d, %Y") -> str:
        current_time = datetime.datetime.now().strftime(format)
        return f"The current time is {current_time}."


class WebTools(ExternalToolsHandler):
    def __init__(self) -> None:
        self.tools: List[FunctionTool] = [
            {
                "type": "function",
                "function": {
                    "name": "http_request",
                    "description": "Send HTTP request to a specified URL.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "description": "HTTP method: GET or POST.",
                            },
                            "url": {
                                "type": "string",
                                "description": "URL to send the request to.",
                            },
                            "headers": {
                                "type": "string",
                                "description": "HTTP JSON headers for the request. This is optional for GET requests.",
                            },
                            "body": {
                                "type": "string",
                                "description": "Body JSON data for POST requests. This is optional for GET requests.",
                            },
                        },
                        "required": ["method", "url", "headers", "body"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
        ]

    def has_function(self, name: str) -> bool:
        return name in ["http_request"]

    def call_function(self, name: str, args: Dict[str, Any]) -> str:
        if name == "http_request":
            return self._http_request(**args)
        return "Unknown function"

    def _http_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=body)
            else:
                return f"Unsupported HTTP method: {method}"
            return f"Response: {response.status_code}, {response.text}"
        except Exception as e:
            return f"HTTP request failed: {str(e)}"
