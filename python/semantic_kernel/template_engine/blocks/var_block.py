# Copyright (c) Microsoft. All rights reserved.

import logging
from re import match as re_match
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Tuple

from pydantic import Field

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.utils.validation import FUNCTION_PARAM_NAME_REGEX

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class VarBlock(Block):
    type: ClassVar[BlockTypes] = BlockTypes.VARIABLE
    name: str = Field("", init=False, exclude=True)

    def model_post_init(self, __context: Any):
        if len(self.content) < 2:
            logger.error("The variable name should not be empty, is %s", self.content)
        else:
            self.name = self.content[1:]

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

        if not re_match(FUNCTION_PARAM_NAME_REGEX, self.name):
            error_msg = (
                f"The variable name '{self.name}' contains invalid characters. "
                "Only alphanumeric chars and underscores are allowed."
            )
            logger.error(error_msg)
            return False, error_msg

        return True, ""

    def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> Any:
        if arguments is None:
            return ""

        if not self.name:
            error_msg = "Variable rendering failed, the variable name is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)

        value = arguments.get(self.name, None)
        if not value:
            logger.warning(f"Variable `{Symbols.VAR_PREFIX}{self.name}` not found in the KernelArguments")

        return value or ""
