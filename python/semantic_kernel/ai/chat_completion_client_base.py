# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from semantic_kernel.ai.chat_request_settings import ChatRequestSettings


class ChatCompletionClientBase(ABC):
    @abstractmethod
    async def complete_chat_async(
        self,
        messages: List[Tuple[str, str]],
        settings: "ChatRequestSettings",
        logger: Logger,
    ) -> str:
        pass
