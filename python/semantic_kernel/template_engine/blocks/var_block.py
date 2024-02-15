# Copyright (c) Microsoft. All rights reserved.

import logging
from re import match as re_match
from typing import Any, Optional, Tuple

import pydantic as pdt

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols

logger: logging.Logger = logging.getLogger(__name__)


class VarBlock(Block):
    _name: str = pdt.PrivateAttr()

    def __init__(self, content: Optional[str] = None, log: Optional[Any] = None):
        super().__init__(content=content and content.strip())

        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")

        if len(self.content) < 2:
            err = "The variable name is empty"
            logger.error(err)
            self._name = ""
            return

        self._name = self.content[1:]

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.VARIABLE

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def is_valid(self) -> Tuple[bool, str]:
        if not self.content:
            error_msg = f"A variable must start with the symbol {Symbols.VAR_PREFIX} " "and have a name"
            logger.error(error_msg)
            return False, error_msg

        if self.content[0] != Symbols.VAR_PREFIX:
            error_msg = f"A variable must start with the symbol {Symbols.VAR_PREFIX}"
            logger.error(error_msg)
            return False, error_msg

        if len(self.content) < 2:
            error_msg = "The variable name is empty"
            logger.error(error_msg)
            return False, error_msg

        if not re_match(r"^[a-zA-Z0-9_]*$", self.name):
            error_msg = (
                f"The variable name '{self.name}' contains invalid characters. "
                "Only alphanumeric chars and underscore are allowed."
            )
            logger.error(error_msg)
            return False, error_msg

        return True, ""

    def render(self, variables: Optional[ContextVariables] = None) -> str:
        if variables is None:
            return ""

        if not self.name:
            error_msg = "Variable rendering failed, the variable name is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)

        value = variables.get(self.name, None)
        if not value:
            logger.warning(f"Variable `{Symbols.VAR_PREFIX}{self.name}` not found")

        return value or ""
