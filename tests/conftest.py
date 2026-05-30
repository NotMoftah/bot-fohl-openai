import os

# set all env vars consumed at module level before lambda_function is imported,
# otherwise boto3 Table construction fails with a missing-identifier error.
os.environ.setdefault("BOT_TOKEN", "test_token")
os.environ.setdefault("DYNAMODB_TABLE_MESSAGES", "test-messages-table")

# dummy aws credentials so boto3 resource construction does not raise
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")
