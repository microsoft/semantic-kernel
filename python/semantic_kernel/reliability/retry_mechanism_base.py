# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class RetryMechanismBase(ABC):
    @abstractmethod
    async def execute_with_retry_async(
        self, action: Callable[[], Awaitable[T]]
    ) -> Awaitable[T]:
        """Executes the given action with retry logic.

        Arguments:
            action {Callable[[], Awaitable[T]]} -- The action to retry on exception.

        Returns:
            Awaitable[T] -- An awaitable that will return the result of the action.
        """
        pass
