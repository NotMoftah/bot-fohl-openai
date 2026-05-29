import os

# ensure a dummy token is present so lambda_function module-level code
# can initialize SendTelegramMessagesHandler without raising at import time.
os.environ.setdefault("BOT_TOKEN", "test_token")
