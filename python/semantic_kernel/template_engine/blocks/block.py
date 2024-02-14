# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import ClassVar, Tuple

from pydantic import field_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

logger: logging.Logger = logging.getLogger(__name__)


class Block(KernelBaseModel):
    type: ClassVar[BlockTypes] = BlockTypes.UNDEFINED
    content: str

    def is_valid(self) -> Tuple[bool, str]:
        raise NotImplementedError("Subclasses must implement this method.")

    @field_validator("content", mode="before")
    @classmethod
    def content_strip(cls, content: str):
        return content.strip()
