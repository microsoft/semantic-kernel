# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple
from logging import Logger

from semantic_kernel.template_engine_v2.blocks.block import Block
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.orchestration.context_variables import ContextVariables


class TextBlock(Block):
    def __init__(
        self,
        text: Optional[str] = None,
        log: Optional[Logger] = None,
        start_index: Optional[int] = None,
        stop_index: Optional[int] = None,
    ):
        if start_index is not None and stop_index is not None:
            if start_index > stop_index:
                raise ValueError(
                    f"start_index ({start_index}) must be less than stop_index ({stop_index})"
                )

            if start_index < 0:
                raise ValueError(f"start_index ({start_index}) must be greater than 0")

            text = text[start_index:stop_index]
        elif start_index is not None:
            text = text[start_index:]
        elif stop_index is not None:
            text = text[:stop_index]

        super().__init__(content=text, log=log)

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.TEXT

    def is_valid(self) -> Tuple[bool, str]:
        return True, ""

    def render(self, _: Optional[ContextVariables] = None) -> str:
        return self.content
