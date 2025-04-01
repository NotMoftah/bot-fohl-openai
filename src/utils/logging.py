import logging

from typing import TypeAlias


class LambdaLogger:
    _Level: TypeAlias = int | str

    def __init__(self, log_level: _Level = None):
        if not log_level:
            log_level = logging.INFO

        if len(logging.getLogger().handlers) > 0:
            logging.getLogger().setLevel(log_level)
        else:
            logging.basicConfig(level=log_level)

        self.logger = logging.getLogger()

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
