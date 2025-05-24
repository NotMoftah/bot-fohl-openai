import datetime
from typing import Optional
from .registry import BaseTool


class GetTimeTool(BaseTool):
    """Tool to get the current time."""

    @property
    def name(self) -> str:
        return "get_time"

    @property
    def description(self) -> str:
        return "Get current time using a specified format."

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
