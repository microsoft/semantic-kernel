# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Union

from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class EchoTextCompletion(TextCompletionClientBase):
    _log: Logger

    def __init__(
        self,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initializes a new instance of the EchoTextCompletion class.

        """
        self._log = logger if logger is not None else NullLogger()

    async def complete_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ) -> Union[str, List[str]]:
        return prompt

    async def complete_stream_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ):
        yield prompt
