# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import ClassVar

from pydantic import field_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

logger: logging.Logger = logging.getLogger(__name__)


class Block(KernelBaseModel):
    """A block."""

    type: ClassVar[BlockTypes] = BlockTypes.UNDEFINED
    content: str

    @field_validator("content", mode="before")
    @classmethod
    def content_strip(cls, content: str):
        """Strip the content of the block."""
        return content.strip()
