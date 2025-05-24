---
applyTo: "*/*.py"
---

# AI Code Conventions - bot-fohl-openai

**Essential coding patterns for AI models working on this codebase.**

## Core Patterns

### Type System

- Import types: `from typing import Dict, List, Any, Optional, Protocol`
- All functions need type hints: `def func(param: str) -> Optional[str]:`
- Use `@dataclass` for data containers
- Use `Protocol` for interfaces, `ABC` for abstract classes

### Naming

- Classes: `PascalCase` (OpenAIChatBot)
- Functions/variables: `snake_case` (send_message, user_id)
- Constants: `UPPER_SNAKE_CASE` (DEFAULT_TOOLS)
- Private: `_underscore_prefix`

### Class Structure

```python
class ExampleClass:
    CONSTANTS = "value"  # Class constants first

    def __init__(self, param: str):  # Constructor
        self.logger = logging.getLogger(self.__class__.__name__)
        self.param = param

    def public_method(self) -> str:  # Public methods
        pass

    def _private_method(self) -> None:  # Private methods
        pass
```

### Imports Order

```python
# 1. Standard library
import json
import logging
from typing import Dict, List, Any, Optional

# 2. Third-party
from openai import AsyncOpenAI
from telegram import Update

# 3. Local imports
from core.context import UserContextManager
from mcp import ToolRegistry
```

### Error Handling Pattern

```python
try:
    result = operation()
    return str(result) if result is not None else ""
except Exception as e:
    self.logger.error(f"Error in operation: {e}", exc_info=True)
    return f"Error: {str(e)}"
```

### Logging Pattern

```python
class MyClass:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def method(self, user_id: str):
        self.logger.info("[User %s] Action performed", user_id)
        self.logger.debug(f"Debug details: {data}")
        self.logger.error(f"Error occurred: {e}", exc_info=True)
```

### Docstring Format

```python
def execute(self, method: str, url: str, headers: Optional[Dict] = None) -> str:
    """
    Brief description of what the function does.

    Args:
        method: HTTP method (GET or POST)
        url: URL to send the request to
        headers: Optional HTTP headers

    Returns:
        HTTP response as a string

    Raises:
        ValueError: If method is not supported
    """
```

## Project Structure

```
src/
├── core/           # Business logic (context, handlers)
├── interfaces/     # External APIs (openai, telegram)
├── tools/          # Tool system (registry, adapters)
└── utils/          # Utilities and helpers
```

## Key Dependencies

- `openai` - Use `AsyncOpenAI` for async operations
- `python-telegram-bot` - Follow async patterns
- `requests` - For HTTP in tools

## AI Guidelines

1. **Match existing patterns** - Follow established code style
2. **Type everything** - Always include type annotations
3. **Log appropriately** - Use class-based loggers with user context
4. **Handle errors** - Try/except with logging and user-friendly messages
5. **Test compatibility** - Ensure changes work with existing tests
6. **Document changes** - Update docstrings when modifying signatures

## Common Code Examples

### Tool Implementation

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass
```

### Async Handler Pattern

```python
async def handle_update(self, update: Update) -> None:
    try:
        user_id = str(update.effective_user.id)
        message = update.message.text

        self.logger.info("[User %s] Processing message", user_id)
        response = await self.chat_bot.send_message(user_id, message)
        await update.message.reply_text(response)

    except Exception as e:
        self.logger.error(f"Error handling update: {e}", exc_info=True)
```

### Configuration Pattern

```python
@dataclass
class Config:
    model: str = "gpt-4o-mini"
    temperature: float = 0.8
    max_tokens: int = 256
```

**Follow these patterns consistently to maintain codebase quality and readability.**
