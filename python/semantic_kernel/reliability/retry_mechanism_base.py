# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional, TypeVar

T = TypeVar("T")

logger: logging.Logger = logging.getLogger(__name__)


class RetryMechanismBase(ABC):
    @abstractmethod
    async def execute_with_retry_async(
        self, action: Callable[[], Awaitable[T]], log: Optional[Any] = None
    ) -> Awaitable[T]:
        """Executes the given action with retry logic.

        Arguments:
            action {Callable[[], Awaitable[T]]} -- The action to retry on exception.

        Returns:
            Awaitable[T] -- An awaitable that will return the result of the action.
        """
        if log:
            logger.warning(
                "The `log` parameter is deprecated. Please use the `logging` module instead."
            )
        pass
