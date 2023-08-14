"""Base class for all AI Services."""
from logging import Logger
from typing import Optional

from semantic_kernel.models.usage_result import UsageResult
from semantic_kernel.utils.null_logger import NullLogger


class AIServiceClientBase:
    """Base class for all AI services."""

    def __init__(self, log: Optional[Logger] = None) -> None:
        self._log: Logger = log or NullLogger()
        self.usage = UsageResult()

    def add_usage(self, usage: UsageResult) -> None:
        """Add usage results."""
        self.usage += usage

    def reset_usage(self) -> None:
        """Reset usage results."""
        self.usage = UsageResult()
