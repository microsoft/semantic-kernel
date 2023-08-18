# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple, Union

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)

from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class EchoChatCompletion(ChatCompletionClientBase, TextCompletionClientBase):
    _log: Logger

    def __init__(
        self,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initializes a new instance of the EchoChatCompletion class.
        """
        self._log = logger if logger is not None else NullLogger()
        self._messages = []

    async def complete_chat_async(
        self,
        messages: List[Tuple[str, str]],
        request_settings: ChatRequestSettings,
        logger: Logger,
    ) -> Union[str, List[str]]:
        return ['_'.join(i) for i in messages]

    async def complete_chat_stream_async(
        self,
        messages: List[Tuple[str, str]],
        request_settings: ChatRequestSettings,
        logger: Logger,
    ):
        yield ['_'.join(i) for i in messages]

    async def complete_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ) -> Union[str, List[str]]:
        return prompt

    async def complete_stream_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ):
        yield prompt
