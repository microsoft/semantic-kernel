# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple

from pydantic import PrivateAttr

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes


class Block(SKBaseModel):
    content: Optional[str] = None

    def __init__(self, content: Optional[str] = None) -> None:
        super().__init__(content=content)

    def is_valid(self) -> Tuple[bool, str]:
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.UNDEFINED
