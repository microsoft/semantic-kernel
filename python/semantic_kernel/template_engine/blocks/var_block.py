# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pydantic import model_validator

from semantic_kernel.exceptions import VarBlockRenderError, VarBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VAR_BLOCK_REGEX = r"^[${1}](?P<name>[0-9A-Za-z_]+)$"

VAR_BLOCK_MATCHER = compile(VAR_BLOCK_REGEX)


class VarBlock(Block):
    """Create a variable block.

    A variable block is used to add a variable to a template.
    It gets rendered from KernelArguments, if the variable is not found
    a warning is logged and an empty string is returned.
    The variable must start with $ and be followed by a valid variable name.
    A valid variable name is a string of letters, numbers and underscores.

    Examples:
        $var
        $test_var

    Args:
        content - str : The content of the variable block, the name of the variable.
        name - str: The name of the variable.

    Raises:
        VarBlockSyntaxError: If the content does not match the variable syntax.

    """

    type: ClassVar[BlockTypes] = BlockTypes.VARIABLE
    name: str = ""

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content and extract the name.

        The parsing is based on a regex that returns the name.
        if the 'name' is already present then the parsing is skipped.
        """
        if isinstance(fields, Block) or "name" in fields:
            return fields
        content = fields.get("content", "").strip()
        matches = VAR_BLOCK_MATCHER.match(content)
        if not matches:
            raise VarBlockSyntaxError(content=content)
        if name := matches.groupdict().get("name"):
            fields["name"] = name
        return fields

    def render(self, _: "Kernel", arguments: Optional["KernelArguments"] = None) -> str:
        """Render the variable block with the given arguments.

        If the variable is not found in the arguments, return an empty string.
        """
        if arguments is None:
            return ""
        value = arguments.get(self.name, None)
        if value is None:
            logger.warning(f"Variable `{Symbols.VAR_PREFIX}: {self.name}` not found in the KernelArguments")
            return ""
        try:
            return str(value)
        except Exception as e:
            raise VarBlockRenderError(
                f"Block {self.name} failed to be parsed to a string, type is {type(value)}"
            ) from e
