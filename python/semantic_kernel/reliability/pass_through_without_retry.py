# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.reliability.retry_mechanism_base import RetryMechanismBase

T = TypeVar("T")

logger: logging.Logger = logging.getLogger(__name__)


class PassThroughWithoutRetry(RetryMechanismBase, KernelBaseModel):
    """A retry mechanism that does not retry."""

    async def execute_with_retry(
        self, action: Callable[[], Awaitable[T]]
    ) -> Awaitable[T]:
        """Executes the given action with retry logic.

        Args:
            action (Callable[[], Awaitable[T]]): The action to retry on exception.

        Returns:
            Awaitable[T]: An awaitable that will return the result of the action.
        """
        try:
            return action()
        except Exception as e:
            logger.warning(e, "Error executing action, not retrying")
            raise e
from typing import Awaitable, Callable, TypeVar

from semantic_kernel.reliability.retry_mechanism import RetryMechanism

T = TypeVar("T")


class PassThroughWithoutRetry(RetryMechanism):
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
