import datetime
from typing import Optional, Dict, Any
from .registry import BaseFunction


class GetTimeFunction(BaseFunction):
    """Function to get the current time."""

    @property
    def name(self) -> str:
        return "get_time"

    @property
    def description(self) -> str:
        return "Get current time using a specified format."

    @property
    def schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for the function, with format parameter explicitly required.
        """
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Python format string for the time",
                }
            },
            "required": ["format"],
            "additionalProperties": False,
        }

    def execute(self, format: str = "%I:%M%p - %B %d, %Y") -> str:
        """
        Get the current time in a specified format.

        Args:
            format: Python format string for the time

        Returns:
            Formatted current time
        """
        current_time = datetime.datetime.now().strftime(format)
        return f"The current time is {current_time}."
