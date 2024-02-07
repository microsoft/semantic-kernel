# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Optional, Tuple

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class TextBlock(Block):
    @classmethod
    def from_text(
        cls,
        text: Optional[str] = None,
        start_index: Optional[int] = None,
        stop_index: Optional[int] = None,
    ):
        if text is None:
            return cls(content="")
        if start_index is not None and stop_index is not None:
            if start_index > stop_index:
                raise ValueError(f"start_index ({start_index}) must be less than " f"stop_index ({stop_index})")

            if start_index < 0:
                raise ValueError(f"start_index ({start_index}) must be greater than 0")

            text = text[start_index:stop_index]
        elif start_index is not None:
            text = text[start_index:]
        elif stop_index is not None:
            text = text[:stop_index]

        return cls(content=text)

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.TEXT

    def is_valid(self) -> Tuple[bool, str]:
        return True, ""

    def render(self, kernel: Optional["Kernel"] = None, arguments: Optional["KernelArguments"] = None) -> str:
        return self.content
