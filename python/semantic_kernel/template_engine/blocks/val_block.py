# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Tuple

from pydantic import Field

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class ValBlock(Block):
    type: ClassVar[BlockTypes] = BlockTypes.VALUE
    first: str = Field("\0", init=False, exclude=True)
    last: str = Field("\0", init=False, exclude=True)
    value: str = Field("", init=False, exclude=True)

    def model_post_init(self, __context: Any):
        if len(self.content) < 2:
            logger.error("A value must have single quotes or double quotes on both sides")
            return
        self.first = self.content[0]
        self.last = self.content[-1]
        self.value = self.content[1:-1]

    def is_valid(self) -> Tuple[bool, str]:
        if self.first not in [Symbols.DBL_QUOTE, Symbols.SGL_QUOTE]:
            error_msg = "A value must be wrapped in either single quotes or double quotes"
            logger.error(error_msg)
            return False, error_msg

        if self.first != self.last:
            error_msg = "A value must be defined using either single quotes or " "double quotes, not both"
            logger.error(error_msg)
            return False, error_msg

        return True, ""

    def render(self, *_: Tuple["Kernel", Optional["KernelArguments"]]) -> str:
        return self.value

    @staticmethod
    def has_val_prefix(text: Optional[str]) -> bool:
        return text is not None and len(text) > 0 and (text[0] == Symbols.DBL_QUOTE or text[0] == Symbols.SGL_QUOTE)
