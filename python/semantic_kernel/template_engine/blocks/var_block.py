# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from re import match as re_match
from typing import Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.protocols.text_renderer import TextRenderer


class VarBlock(Block, TextRenderer):
    def __init__(self, content: Optional[str] = None, log: Optional[Logger] = None):
        super().__init__(content=content and content.strip(), log=log)

        if len(self.content) < 2:
            err = "The variable name is empty"
            self.log.error(err)
            self.name = ""
            return

        self.name = self.content[1:]

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.VARIABLE

    def is_valid(self) -> Tuple[bool, str]:
        if not self.content:
            error_msg = (
                f"A variable must start with the symbol {Symbols.VAR_PREFIX} "
                "and have a name"
            )
            self.log.error(error_msg)
            return False, error_msg

        if self.content[0] != Symbols.VAR_PREFIX:
            error_msg = f"A variable must start with the symbol {Symbols.VAR_PREFIX}"
            self.log.error(error_msg)
            return False, error_msg

        if len(self.content) < 2:
            error_msg = "The variable name is empty"
            self.log.error(error_msg)
            return False, error_msg

        if not re_match(r"^[a-zA-Z0-9_]*$", self.name):
            error_msg = (
                f"The variable name '{self.name}' contains invalid characters. "
                "Only alphanumeric chars and underscore are allowed."
            )
            self.log.error(error_msg)
            return False, error_msg

        return True, ""

    def render(self, variables: Optional[ContextVariables] = None) -> str:
        if variables is None:
            return ""

        if not self.name:
            error_msg = "Variable rendering failed, the variable name is empty"
            self.log.error(error_msg)
            raise ValueError(error_msg)

        exists, value = variables.get(self.name)
        if not exists:
            self.log.warning(f"Variable `{Symbols.VAR_PREFIX}{self.name}` not found")

        return value if exists else ""
