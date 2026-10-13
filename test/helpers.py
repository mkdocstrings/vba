"""
Provide warning assertions for every supported Python version.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator


class _WarningCapture(logging.Handler):
    """
    Record warning and error messages during an assertion.
    """

    def __init__(self) -> None:
        """
        Initialize a handler that records warnings and errors.
        """
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """
        Record a warning or error.

        Args:
            record: Log record delivered by the logging framework.
        """
        self.messages.append(f"{record.levelname}:{record.name}:{record.getMessage()}")


@contextmanager
def assert_no_warnings() -> Iterator[None]:
    """
    Fail when the enclosed operation logs a warning or error.

    Yields:
        No value; checks captured messages on normal context exit.

    Raises:
        AssertionError: If any warning or error was logged.
    """
    # TestCase.assertNoLogs requires Python >=3.10.
    # Remove this helper when the minimum tested Python becomes 3.10.
    logger = logging.getLogger()
    previous_level = logger.level
    capture = _WarningCapture()
    logger.addHandler(capture)
    logger.setLevel(logging.WARNING)
    try:
        yield
        if capture.messages:
            raise AssertionError(f"Unexpected warning logs: {capture.messages}")
    finally:
        logger.removeHandler(capture)
        logger.setLevel(previous_level)
        capture.close()
