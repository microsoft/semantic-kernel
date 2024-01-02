# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, Optional, Tuple

import pydantic as pdt

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols

logger: logging.Logger = logging.getLogger(__name__)


class ValBlock(Block):
    _first: str = pdt.PrivateAttr()
    _last: str = pdt.PrivateAttr()
    _value: str = pdt.PrivateAttr()

    def __init__(self, content: Optional[str] = None, log: Optional[Any] = None):
        super().__init__(content=content and content.strip())

        if log:
            logger.warning(
                "The `log` parameter is deprecated. Please use the `logging` module instead."
            )

        if len(self.content) < 2:
            err = "A value must have single quotes or double quotes on both sides"
            logger.error(err)
            self._value = ""
            self._first = "\0"
            self._last = "\0"
            return

        self._first = self.content[0]
        self._last = self.content[-1]
        self._value = self.content[1:-1]

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.VALUE

    def is_valid(self) -> Tuple[bool, str]:
        if len(self.content) < 2:
            error_msg = "A value must have single quotes or double quotes on both sides"
            logger.error(error_msg)
            return False, error_msg

        if self._first != Symbols.DBL_QUOTE and self._first != Symbols.SGL_QUOTE:
            error_msg = (
                "A value must be wrapped in either single quotes or double quotes"
            )
            logger.error(error_msg)
            return False, error_msg

        if self._first != self._last:
            error_msg = (
                "A value must be defined using either single quotes or "
                "double quotes, not both"
            )
            logger.error(error_msg)
            return False, error_msg

        return True, ""

    def render(self, _: Optional[ContextVariables] = None) -> str:
        return self._value

    @staticmethod
    def has_val_prefix(text: Optional[str]) -> bool:
        return (
            text is not None
            and len(text) > 0
            and (text[0] == Symbols.DBL_QUOTE or text[0] == Symbols.SGL_QUOTE)
        )
