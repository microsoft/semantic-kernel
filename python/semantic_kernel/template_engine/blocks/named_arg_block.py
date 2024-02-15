# Copyright (c) Microsoft. All rights reserved.

import logging
from re import match as re_match
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Tuple, Union

from pydantic import Field

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.utils.validation import NAMED_ARG_REGEX

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class NamedArgBlock(Block):
    type: ClassVar[BlockTypes] = BlockTypes.NAMED_ARG
    name: Optional[VarBlock] = Field(None, init=False, exclude=True)
    value: Optional[Union[VarBlock, ValBlock]] = Field(None, init=False, exclude=True)

    def model_post_init(self, __context: Any):
        if len(self.content) < 3:
            logger.error("The argument name and the value cannot be empty, is %s", self.content)
        else:
            match = re_match(NAMED_ARG_REGEX, self.content)
            if match:
                self.name = VarBlock(content=f"{Symbols.VAR_PREFIX.value}{match.group('name')}")
                value = match.group("value")
                if value[0] == Symbols.VAR_PREFIX:
                    self.value = VarBlock(content=value)
                else:
                    self.value = ValBlock(content=value)
            else:
                logger.error("The argument '%s' is not a valid named argument", self.content)

    def is_valid(self) -> Tuple[bool, str]:
        if not self.content:
            error_msg = (
                f"A variable must be at least three characters, with a {Symbols.NAMED_ARG_BLOCK_SEPARATOR}"
                f"and a valid name for the argument and a value, with or without the symbol {Symbols.VAR_PREFIX}"
            )
            logger.error(error_msg)
            return False, error_msg

        if not re_match(NAMED_ARG_REGEX, self.content):
            error_msg = (
                f"The variable name '{self.content}' contains invalid characters. "
                f"Should have a '{Symbols.NAMED_ARG_BLOCK_SEPARATOR}' and a proper name for the argument and a value,"
                f"with or without the symbol '{Symbols.VAR_PREFIX}'"
            )
            logger.error(error_msg)
            return False, error_msg

        return True, ""

    def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> Any:
        if self.value.type == BlockTypes.VALUE:
            return self.value.render(kernel, arguments)
        if arguments is None:
            return ""
        if self.value.type == BlockTypes.VARIABLE:
            return self.value.render(kernel, arguments)
