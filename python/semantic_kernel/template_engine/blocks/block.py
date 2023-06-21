# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Optional, Tuple

from semantic_kernel.orchestration.callback_handler_base import CallbackHandlerBase
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.utils.null_logger import NullLogger


class Block:
    def __init__(
        self,
        content: Optional[str] = None,
        log: Optional[Logger] = NullLogger,
        handler: CallbackHandlerBase = None,
    ) -> None:
        self._content = content or ""
        self._log = log or NullLogger()
        self._type = BlockTypes.UNDEFINED
        self._handler = handler or CallbackHandlerBase()

    @property
    def type(self) -> BlockTypes:
        return self._type

    @property
    def content(self) -> str:
        return self._content

    @property
    def log(self) -> Logger:
        return self._log

    def is_valid(self) -> Tuple[bool, str]:
        raise NotImplementedError("Subclasses must implement this method.")
