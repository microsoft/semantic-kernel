# Copyright (c) Microsoft. All rights reserved.

import logging
from re import S, compile
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import model_validator

from semantic_kernel.exceptions import ValBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VAL_BLOCK_REGEX = r"^(?P<quote>[\"'])(?P<value>.*)(?P=quote)$"

VAL_BLOCK_MATCHER = compile(VAL_BLOCK_REGEX, flags=S)


class ValBlock(Block):
    """Create a value block.

    A value block is used to represent a value in a template.
    It can be used to represent any characters.
    It needs to start and end with the same quote character,
    can be both single or double quotes, as long as they are not mixed.

    Examples:
        'value'
        "value"
        'value with "quotes"'
        "value with 'quotes'"

    Args:
        content - str : The content of the value block.
        value - str: The value of the block.
        quote - str: The quote used to wrap the value.

    Raises:
        ValBlockSyntaxError: If the content does not match the value block syntax.

    """

    type: ClassVar[BlockTypes] = BlockTypes.VALUE
    value: str | None = ""
    quote: str | None = "'"

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        """Parse the content and extract the value and quote.

        The parsing is based on a regex that returns the value and quote.
        if the 'value' is already present then the parsing is skipped.
        """
        if isinstance(fields, Block) or "value" in fields:
            return fields
        content = fields.get("content", "").strip()
        matches = VAL_BLOCK_MATCHER.match(content)
        if not matches:
            raise ValBlockSyntaxError(content=content)
        if value := matches.groupdict().get("value"):
            fields["value"] = value
        if quote := matches.groupdict().get("quote"):
            fields["quote"] = quote
        return fields

    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the value block."""
        return self.value or ""
