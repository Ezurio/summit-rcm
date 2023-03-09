from logging import Logger, NOTSET, LogRecord, ERROR
from typing import Any


class BleLogger(Logger):
    """
    Wrap logger such that we can hook it for returning logged errors and/or info items
    over REST API.
    """

    def __init__(self, name, level=NOTSET):
        self.error_occurred: bool = False
        self.last_message: str = ""
        super(BleLogger, self).__init__(name, level)

    def handle(self, record: LogRecord) -> None:
        self.last_message = record.getMessage()
        if record.levelname == "ERROR":
            self.error_occurred = True
        return super(BleLogger, self).handle(record)

    def log(
        self,
        level: int,
        msg: Any,
        *args: Any,
        exc_info=...,
        stack_info: bool = ...,
        stacklevel: int = ...,
        extra=...,
        **kwargs: Any,
    ) -> None:
        if level == ERROR:
            self.error_occurred = True
        return super(BleLogger, self).log(
            level, msg, args, exc_info, stack_info, stacklevel, extra, kwargs
        )
