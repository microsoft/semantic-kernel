# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes


class TextBlock(Block):
    @classmethod
    def from_text(
        cls,
        text: Optional[str] = None,
        start_index: Optional[int] = None,
        stop_index: Optional[int] = None,
        log: Optional[Logger] = None,
    ):
        if text is None:
            return cls(content="", log=log)
        if start_index is not None and stop_index is not None:
            if start_index > stop_index:
                raise ValueError(
                    f"start_index ({start_index}) must be less than "
                    f"stop_index ({stop_index})"
                )

            if start_index < 0:
                raise ValueError(f"start_index ({start_index}) must be greater than 0")

            text = text[start_index:stop_index]
        elif start_index is not None:
            text = text[start_index:]
        elif stop_index is not None:
            text = text[:stop_index]

        return cls(content=text, log=log)

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.TEXT

    def is_valid(self) -> Tuple[bool, str]:
        return True, ""

    def render(self, _: Optional[ContextVariables] = None) -> str:
        return self.content
