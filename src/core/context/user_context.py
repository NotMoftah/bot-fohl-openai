from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class UserContext:
    """
    Represents a chat context for a specific user.
    Stores conversation history and user-specific settings.
    """

    user_id: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the user's conversation history."""
        self.history.append(message)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the user's conversation history."""
        return self.history

    def clear_history(self) -> None:
        """Clear the user's conversation history."""
        self.history.clear()

    def add_system_message(self, content: str) -> None:
        """Add a system message to the user's conversation history."""
        self.history.append({"role": "system", "content": content})

    def get_history_with_system_message(
        self, system_message: str
    ) -> List[Dict[str, Any]]:
        """Get user history with a specific system message at the beginning."""
        # Check if there's already a system message
        if self.history and self.history[0].get("role") == "system":
            # Clone history but replace system message
            result = self.history.copy()
            result[0] = {"role": "system", "content": system_message}
            return result
        else:
            # Add system message at the beginning
            return [{"role": "system", "content": system_message}] + self.history


class UserContextManager:
    """
    Manages conversation contexts for multiple users.
    Ensures each user has their own separate chat history.
    """

    def __init__(self):
        self.contexts: Dict[str, UserContext] = {}

    def get_context(self, user_id: str) -> UserContext:
        """
        Get a user's context, creating it if it doesn't exist.

        Args:
            user_id: The unique identifier for the user

        Returns:
            The user's context
        """
        if user_id not in self.contexts:
            self.contexts[user_id] = UserContext(user_id=user_id)
        return self.contexts[user_id]

    def save_context(self, user_id: str, context: UserContext) -> None:
        """
        Save a user's context.

        Args:
            user_id: The unique identifier for the user
            context: The user's context to save
        """
        self.contexts[user_id] = context

    def delete_context(self, user_id: str) -> None:
        """
        Delete a user's context.

        Args:
            user_id: The unique identifier for the user
        """
        if user_id in self.contexts:
            del self.contexts[user_id]
