# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Optional, Tuple

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

logger: logging.Logger = logging.getLogger(__name__)


class Block(KernelBaseModel):
    content: Optional[str] = None

    def is_valid(self) -> Tuple[bool, str]:
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.UNDEFINED
