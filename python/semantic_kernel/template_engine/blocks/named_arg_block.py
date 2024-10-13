# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pydantic import model_validator

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
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
<<<<<<< HEAD
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
=======
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import NamedArgBlockSyntaxError
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

NAMED_ARG_REGEX = r"^(?P<name>[0-9A-Za-z_]+)[=]{1}(?P<value>[${1}](?P<var_name>[0-9A-Za-z_]+)|(?P<quote>[\"'])(?P<val>.[^\"^']*)(?P=quote))$"  # noqa: E501

NAMED_ARG_MATCHER = compile(NAMED_ARG_REGEX)


class NamedArgBlock(Block):
    """Create a named argument block.

    A named arg block is used to add arguments to a function call.
    It needs to be combined with a function_id block to be useful.
    Inside a code block, if the first block is a function_id block,
    the first block can be a variable or value block, anything else
    must be a named arg block.

    The value inside the NamedArgBlock can be a ValBlock or a VarBlock.

    Examples:
        {{ plugin.function arg1=$var }}
        {{ plugin.function arg1='value' }}
        {{ plugin.function 'value' arg2=$var }}
        {{ plugin.function $var arg2='value' }}
        {{ plugin_function arg1=$var1 arg2=$var2 arg3='value' }}

    Args:
        content - str : The content of the named argument block,
            the name and value separated by an equal sign, for instance arg1=$var.
        name - str: The name of the argument.
        value - ValBlock: The value of the argument.
        variable - VarBlock: The variable of the argument.
            Either the value or variable field is used.

    Raises:
        NamedArgBlockSyntaxError: If the content does not match the named argument syntax.

    """

    type: ClassVar[BlockTypes] = BlockTypes.NAMED_ARG
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
    name: str | None = None
    value: ValBlock | None = None
    variable: VarBlock | None = None
=======
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    name: str | None = None
    value: ValBlock | None = None
    variable: VarBlock | None = None
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    name: str | None = None
    value: ValBlock | None = None
    variable: VarBlock | None = None
=======
    name: Optional[str] = None
    value: Optional[ValBlock] = None
    variable: Optional[VarBlock] = None
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content of the named argument block and extract the name and value.

        If the name and either value or variable is present the parsing is skipped.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Otherwise, the content is parsed using a regex to extract the name and value.
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
<<<<<<< HEAD
        Otherwise, the content is parsed using a regex to extract the name and value.
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        Otherwise, the content is parsed using a regex to extract the name and value.
=======
>>>>>>> Stashed changes
=======
        Otherwise, the content is parsed using a regex to extract the name and value.
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        Otherwise, the content is parsed using a regex to extract the name and value.
=======
        Otherwise the content is parsed using a regex to extract the name and value.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        Those are then turned into Blocks.

        Raises:
            NamedArgBlockSyntaxError: If the content does not match the named argument syntax.
        """
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
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
        if isinstance(fields, Block) or (
            "name" in fields and ("value" in fields or "variable" in fields)
        ):
=======
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        if isinstance(fields, Block) or (
            "name" in fields and ("value" in fields or "variable" in fields)
        ):
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        if isinstance(fields, Block) or (
            "name" in fields and ("value" in fields or "variable" in fields)
        ):
=======
        if isinstance(fields, Block) or ("name" in fields and ("value" in fields or "variable" in fields)):
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
            return fields
        content = fields.get("content", "").strip()
        matches = NAMED_ARG_MATCHER.match(content)
        if not matches:
            raise NamedArgBlockSyntaxError(content=content)
        matches_dict = matches.groupdict()
        if name := matches_dict.get("name"):
            fields["name"] = name
        if value := matches_dict.get("value"):
            if matches_dict.get("var_name"):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
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
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                fields["variable"] = VarBlock(
                    content=value, name=matches_dict["var_name"]
                )
            elif matches_dict.get("val"):
                fields["value"] = ValBlock(
                    content=value,
                    value=matches_dict["val"],
                    quote=matches_dict["quote"],
                )
        return fields

    def render(
        self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None
    ) -> Any:
        """Render the named argument block."""
        if self.value:
            return self.value.render()
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
                fields["variable"] = VarBlock(content=value, name=matches_dict["var_name"])
            elif matches_dict.get("val"):
                fields["value"] = ValBlock(content=value, value=matches_dict["val"], quote=matches_dict["quote"])
        return fields

    def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> Any:
        if self.value:
            return self.value.render(kernel, arguments)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        if arguments is None:
            return ""
        if self.variable:
            return self.variable.render(kernel, arguments)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return None
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
<<<<<<< HEAD
        return None
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        return None
=======
>>>>>>> Stashed changes
=======
        return None
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        return None
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
