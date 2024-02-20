# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pydantic import model_validator

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
    type: ClassVar[BlockTypes] = BlockTypes.VARIABLE
    name: Optional[str] = ""

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> Any:
        if isinstance(fields, Block) or "name" in fields:
            return fields
        content = fields.get("content", "").strip()
        matches = VAR_BLOCK_MATCHER.match(content)
        if not matches:
            raise ValueError("The content should be a valid variable block.")
        if name := matches.groupdict().get("name"):
            fields["name"] = name
        return fields

    def render(self, _: "Kernel", arguments: Optional["KernelArguments"] = None) -> Any:
        if arguments is None:
            return ""
        value = arguments.get(self.name, None)
        if not value:
            logger.warning(f"Variable `{Symbols.VAR_PREFIX}{self.name}` not found in the KernelArguments")
        return value or ""
