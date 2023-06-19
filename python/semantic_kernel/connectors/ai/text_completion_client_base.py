# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING

from semantic_kernel.orchestration.sk_context import SKContext

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.complete_request_settings import (
        CompleteRequestSettings,
    )


class TextCompletionClientBase(ABC):
    @abstractmethod
    async def complete_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        context: "SKContext",
        logger: Logger,
    ) -> str:
        pass

    @abstractmethod
    async def complete_stream_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        context: "SKContext",
        logger: Logger,
    ):
        pass
