# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import model_validator

from semantic_kernel.exceptions import FunctionIdBlockSyntaxError
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

FUNCTION_ID_BLOCK_REGEX = r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"

FUNCTION_ID_BLOCK_MATCHER = compile(FUNCTION_ID_BLOCK_REGEX)


class FunctionIdBlock(Block):
    """Block to represent a function id. It can be used to call a function from a plugin.

    The content is parsed using a regex, that returns either a plugin and
    function name or just a function name, depending on the content.

    Anything other than that and a ValueError is raised.

    Args:
        content (str): The content of the block.
        function_name (Optional[str], optional): The function name.
        plugin_name (Optional[str], optional): The plugin name.

    Raises:
        ValueError: If the content does not have valid syntax.
    """

    type: ClassVar[BlockTypes] = BlockTypes.FUNCTION_ID
    function_name: str = ""
    plugin_name: str | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Any) -> dict[str, Any]:
        """Parse the content of the function id block and extract the plugin and function name.

        If both are present in the fields, return the fields as is.
        Otherwise, use the regex to extract the plugin and function name.
        """
        if isinstance(fields, dict):
            if "plugin_name" in fields and "function_name" in fields:
                return fields
            content = fields.get("content", "").strip()
            matches = FUNCTION_ID_BLOCK_MATCHER.match(content)
            if not matches:
                raise FunctionIdBlockSyntaxError(content=content)
            if plugin := matches.groupdict().get("plugin"):
                fields["plugin_name"] = plugin
            fields["function_name"] = matches.group("function")
        return fields

    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
        return self.content
