# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Awaitable, Callable, TypeVar

from semantic_kernel.reliability.retry_mechanism_base import RetryMechanismBase
from semantic_kernel.sk_pydantic import PydanticField

T = TypeVar("T")


class PassThroughWithoutRetry(RetryMechanismBase, PydanticField):
    """A retry mechanism that does not retry."""

    async def execute_with_retry_async(
        self, action: Callable[[], Awaitable[T]], log: logging.Logger
    ) -> Awaitable[T]:
        """Executes the given action with retry logic.

        Arguments:
            action {Callable[[], Awaitable[T]]} -- The action to retry on exception.
            log {logging.Logger} -- The logger to use.

        Returns:
            Awaitable[T] -- An awaitable that will return the result of the action.
        """
        try:
            await action()
        except Exception as e:
            log.warning(e, "Error executing action, not retrying")
            raise
