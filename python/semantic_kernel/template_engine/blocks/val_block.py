# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Tuple

from pydantic import model_validator

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VAL_BLOCK_REGEX = r"^(?P<quote>[\"'])(?P<value>.*)(?P=quote)$"

VAL_BLOCK_MATCHER = compile(VAL_BLOCK_REGEX)


class ValBlock(Block):
    type: ClassVar[BlockTypes] = BlockTypes.VALUE
    value: Optional[str] = ""
    quote: Optional[str] = "'"

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        # when a instance is used as a field this method is called as well
        if isinstance(fields, Block) or "value" in fields:
            return fields
        content = fields.get("content", "").strip()
        matches = VAL_BLOCK_MATCHER.match(content)
        if not matches:
            raise ValueError("The content should be a valid value block.")
        if value := matches.groupdict().get("value"):
            fields["value"] = value
        if quote := matches.groupdict().get("quote"):
            fields["quote"] = quote
        return fields

    def render(self, *_: Tuple["Kernel", Optional["KernelArguments"]]) -> str:
        return self.value
