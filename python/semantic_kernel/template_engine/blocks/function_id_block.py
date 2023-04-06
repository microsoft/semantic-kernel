# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from re import match as re_match
from typing import Optional, Tuple

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.protocols.text_renderer import TextRenderer


class FunctionIdBlock(Block, TextRenderer):
    def __init__(self, content: Optional[str] = None, log: Optional[Logger] = None):
        super().__init__(content=content and content.strip(), log=log)

        function_name_parts = self.content.split(".")
        if len(function_name_parts) > 2:
            self.log.error(f"Invalid function name `{self.content}`")
            raise ValueError(
                "A function name can contain at most one dot separating "
                "the skill name from the function name"
            )

        if len(function_name_parts) == 2:
            self.skill_name = function_name_parts[0]
            self.function_name = function_name_parts[1]
        else:
            self.skill_name = ""
            self.function_name = self.content

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.FUNCTION_ID

    def is_valid(self) -> Tuple[bool, str]:
        if self.content is None or len(self.content) == 0:
            error_msg = "The function identifier is empty"
            return False, error_msg

        if not re_match(r"^[a-zA-Z0-9_.]*$", self.content):
            # NOTE: this is not quite the same as
            # utils.validation.validate_function_name
            error_msg = (
                f"The function identifier '{self.content}' contains invalid "
                "characters. Only alphanumeric chars, underscore and a single "
                "dot are allowed."
            )
            return False, error_msg

        if self._has_more_than_one_dot(self.content):
            error_msg = (
                "The function identifier can contain max one '.' "
                "char separating skill name from function name"
            )
            return False, error_msg

        return True, ""

    def render(self, _: Optional[ContextVariables] = None) -> str:
        return self.content

    def _has_more_than_one_dot(self, value: Optional[str]) -> bool:
        if value is None or len(value) < 2:
            return False

        count = 0
        for char in value:
            if char == ".":
                count += 1
                if count > 1:
                    return True

        return False
