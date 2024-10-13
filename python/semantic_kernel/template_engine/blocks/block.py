# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import ClassVar

from pydantic import field_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

logger: logging.Logger = logging.getLogger(__name__)


class Block(KernelBaseModel):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
    """A block."""

    type: ClassVar[BlockTypes] = BlockTypes.UNDEFINED
    content: str

    @field_validator("content", mode="before")
    @classmethod
    def content_strip(cls, content: str):
        """Strip the content of the block."""
        return content.strip()
from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.template_engine.blocks.block_types import BlockTypes


class Block(ABC):
    _type: BlockTypes
    _content: str
    _log: Logger

    def __init__(self, block_type: BlockTypes, content: str, log: Logger) -> None:
        self._type = block_type
        self._content = content
        self._log = log

    async def render_code_async(self, context: SKContext) -> str:
        raise NotImplementedError("This block does not support code execution")

    @abstractmethod
    def is_valid(self) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def render(self, variables: Optional[ContextVariables]) -> str:
        pass

    @property
    def type(self) -> BlockTypes:
        return self._type

    @property
    def content(self) -> str:
        return self._content
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    type: ClassVar[BlockTypes] = BlockTypes.UNDEFINED
    content: str

    @field_validator("content", mode="before")
    @classmethod
    def content_strip(cls, content: str):
        return content.strip()
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
