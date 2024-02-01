# Copyright (c) Microsoft. All rights reserved.

import logging
from re import match as re_match
from typing import TYPE_CHECKING, Optional, Tuple

from pydantic import Field

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.orchestration.kernel_arguments import KernelArguments

logger: logging.Logger = logging.getLogger(__name__)


class FunctionIdBlock(Block):
    plugin_name: str = Field(init_var=False)
    function_name: str = Field(init_var=False)

    def __init__(self, content: Optional[str] = None):
        super().__init__(content=content and content.strip())

        function_name_parts = self.content.split(".")
        if len(function_name_parts) > 2:
            logger.error(f"Invalid function name `{self.content}`")
            raise ValueError(
                "A function name can contain at most one dot separating " "the plugin name from the function name"
            )

        if len(function_name_parts) == 2:
            self.plugin_name = function_name_parts[0]
            self.function_name = function_name_parts[1]
        else:
            self.plugin_name = ""
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

        if self.content.count(".") > 1:
            error_msg = (
                "The function identifier can contain max one '.' " "char separating plugin name from function name"
            )
            return False, error_msg

        return True, ""

    def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> str:
        return self.content
