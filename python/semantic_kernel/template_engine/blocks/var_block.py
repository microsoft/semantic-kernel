# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from re import match as regex_match
from typing import Literal, Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.template_exception import TemplateException
from semantic_kernel.utils.static_property import static_property


class VarBlock(Block):
    _name: str

    def __init__(self, content: str, log: Logger) -> None:
        super().__init__(BlockTypes.Variable, content, log)

    def is_valid(self) -> Tuple[bool, str]:
        error = ""

        if self._content is None:
            error = "This variable's content is None"
        elif self._content.strip() == "":
            error = "This variable's content is empty"
        elif self._content[0] != VarBlock.PREFIX:
            error = f"A variable must start with the symbol {VarBlock.PREFIX}"
        elif not self.is_valid_var_name(self.name):
            error = (
                f"The variable name '{self.name}' contains invalid characters."
                " Only alphanumeric characters and underscores are allowed."
            )

        if error != "":
            self._log.error(error)
            return False, error

        return True, ""

    def render(self, variables: Optional[ContextVariables]) -> str:
        if variables is None:
            return ""

        if self.name is not None and self.name.strip() != "":
            exists, value = variables.get(self.name)

            if not exists:
                self._log.warning(f"Variable {VarBlock.PREFIX}{self.name} not found")

            return value if exists else ""

        self._log.error("Variable rendering failed, the variable name is None or empty")
        raise TemplateException(
            TemplateException.ErrorCodes.SyntaxError,
            "Variable rendering failed, the variable name is None or empty",
        )

    @property
    def name(self) -> str:
        if self._content is None or len(self._content) < 2:
            return ""

        return self._content[1:]

    @staticmethod
    def has_var_prefix(text: str) -> bool:
        return text is not None and text.strip() != "" and text[0] == VarBlock.PREFIX

    @staticmethod
    def is_valid_var_name(text: str) -> bool:
        return regex_match(r"^[a-zA-Z0-9_]*$", text) is not None

    @static_property
    def PREFIX() -> Literal["$"]:
        return "$"
