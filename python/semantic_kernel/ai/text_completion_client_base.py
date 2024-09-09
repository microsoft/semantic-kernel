# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.ai.complete_request_settings import CompleteRequestSettings


class TextCompletionClientBase(ABC):
    @abstractmethod
    async def complete_simple_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        logger: Logger,
    ) -> str:
        pass
