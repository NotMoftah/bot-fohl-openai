"""Root pytest configuration — runs before any test module is imported."""

import os

# ensure a dummy token is present so lambda_function module-level code
# can initialise SendTelegramMessagesHandler without raising at import time.
os.environ.setdefault("BOT_TOKEN", "test_token")
