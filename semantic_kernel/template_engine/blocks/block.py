# Copyright (c) Microsoft. All rights reserved.

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
