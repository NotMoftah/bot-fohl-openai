# FOHL-FEH Telegram Bot

A Telegram bot that uses OpenAI's API to process messages, with support for custom tools and per-user conversation contexts.

## Architecture

The project has been refactored into a more modular and maintainable architecture:

```
src/
├── __init__.py             # Package root
├── __main__.py             # Entry point for local testing
├── lambda_function.py      # AWS Lambda entry point
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── context/            # User context management
│   │   ├── __init__.py
│   │   └── user_context.py
│   └── tool_handler.py     # Legacy tool handler interface
├── interfaces/             # External APIs
│   ├── __init__.py
│   ├── openai/             # OpenAI integration
│   │   ├── __init__.py
│   │   └── chat_bot.py     # OpenAI chat bot implementation
│   └── telegram/           # Telegram integration
│       ├── __init__.py
│       ├── interface.py    # Telegram bot interface
│       ├── message.py      # Telegram message wrapper
│       └── parsers.py      # Telegram request parsers
├── infrastructure/         # Infrastructure components
│   ├── __init__.py
│   └── lambda_handler.py   # AWS Lambda handler implementation
└── tools/                  # Tool implementations
    ├── __init__.py
    ├── registry.py         # Tool registry
    ├── legacy_adapter.py   # Adapter for legacy tool handlers
    ├── time_tools.py       # Time-related tools
    └── web_tools.py        # Web-related tools
```

## Key Features

- **Per-User Context**: Each user now has a separate conversation context, ensuring privacy and personalization.
- **Modular Tool System**: Tools are now registered and managed through a central registry.
- **Simplified Tool Creation**: New tools can be created by implementing the Tool interface or extending BaseTool.
- **Local Testing**: A new `__main__.py` script allows for local testing without deploying to AWS Lambda.
- **Improved Error Handling**: Better error handling and logging throughout the codebase.

## Running Locally

1. Create a `.env` file with your API keys:

```
BOT_TOKEN=your_telegram_bot_token
GPT_TOKEN=your_openai_api_key
GPT_MODEL=gpt-4o-mini
GPT_TEMPERATURE=0.8
GPT_SYSTEM_MESSAGE="You are a helpful assistant that always responds in raw text format."
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Run the bot locally:

```bash
python -m src
```

You can also specify command-line options:

```bash
python -m src --model gpt-4o --temperature 0.7
```

## Deploying to AWS Lambda

The bot is designed to be deployed as an AWS Lambda function:

1. Package the code and dependencies:

```bash
# Using the provided script
./tools/aws-lambda-layers/generate.ps1
```

2. Upload the resulting package to AWS Lambda.

3. Configure environment variables in AWS Lambda:

   - `BOT_TOKEN`: Your Telegram bot token
   - `GPT_TOKEN`: Your OpenAI API key
   - `GPT_MODEL` (optional): OpenAI model to use
   - `GPT_TEMPERATURE` (optional): Temperature for model responses
   - `GPT_SYSTEM_MESSAGE` (optional): System message for the assistant

4. Set the handler to `src.lambda_function.lambda_handler`.

## Creating Custom Tools

You can create custom tools by implementing the Tool interface or extending BaseTool:

```python
from mcp import BaseTool

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"

    @property
    def description(self) -> str:
        return "Description of my custom tool"

    def execute(self, param1: str, param2: int = 42) -> str:
        # Implementation
        return f"Processed {param1} with {param2}"
```

Then register your tool with the OpenAI chat bot:

```python
from mcp import ToolRegistry, MyCustomTool

# Create tool registry
tool_registry = ToolRegistry()

# Register your custom tool
tool_registry.register_tool(MyCustomTool())

# Create OpenAI chat bot with the tool registry
chatbot = OpenAIChatBot(
    api_key=gpt_token,
    tool_registry=tool_registry
)
```

## Legacy Tool Support

The refactored code maintains backward compatibility with the old tool system:

```python
from core import ExternalToolsHandler

class MyLegacyHandler(ExternalToolsHandler):
    def __init__(self):
        super().__init__()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "legacy_function",
                    # ...
                }
            }
        ]

    def has_function(self, name: str) -> bool:
        return name == "legacy_function"

    def call_function(self, name: str, args: dict) -> str:
        if name == "legacy_function":
            # Implementation
            return "Result"
        return "Unknown function"

# Register with OpenAI chat bot
chatbot.register_external_tools(MyLegacyHandler())
```
