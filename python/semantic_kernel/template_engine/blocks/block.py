# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, Optional, Tuple

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

logger: logging.Logger = logging.getLogger(__name__)


class Block(KernelBaseModel):
    content: Optional[str] = None

    def __init__(self, content: Optional[str] = None, log: Optional[Any] = None) -> None:
        super().__init__(content=content)

        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")

    def is_valid(self) -> Tuple[bool, str]:
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.UNDEFINED
