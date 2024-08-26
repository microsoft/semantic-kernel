# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

logger: logging.Logger = logging.getLogger(__name__)


class RetryMechanismBase(ABC):
    """Base class for retry mechanisms."""

    @abstractmethod
    async def execute_with_retry(
        self, action: Callable[[], Awaitable[T]]
    ) -> Awaitable[T]:
        """Executes the given action with retry logic.

        Args:
            action (Callable[[], Awaitable[T]]): The action to retry on exception.

        Returns:
            Awaitable[T]: An awaitable that will return the result of the action.
        """
