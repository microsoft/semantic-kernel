# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, Awaitable, Callable, Optional, TypeVar

from semantic_kernel.reliability.retry_mechanism_base import RetryMechanismBase
from semantic_kernel.sk_pydantic import SKBaseModel

T = TypeVar("T")

logger: logging.Logger = logging.getLogger(__name__)


class PassThroughWithoutRetry(RetryMechanismBase, SKBaseModel):
    """A retry mechanism that does not retry."""

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
        try:
            await action()
        except Exception as e:
            logger.warning(e, "Error executing action, not retrying")
            raise
