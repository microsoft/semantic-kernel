# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import model_validator

from semantic_kernel.exceptions import FunctionIdBlockSyntaxError
<<<<<<< Updated upstream
from semantic_kernel.template_engine.blocks.block import Block
=======
<<<<<<< main
=======
=======
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Tuple

from pydantic import model_validator

>>>>>>> ms/small_fixes
>>>>>>> origin/main
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import FunctionIdBlockSyntaxError
>>>>>>> Stashed changes
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)
<<<<<<< Updated upstream

FUNCTION_ID_BLOCK_REGEX = (
    r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
)
=======
<<<<<<< main

FUNCTION_ID_BLOCK_REGEX = (
    r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
)

FUNCTION_ID_BLOCK_MATCHER = compile(FUNCTION_ID_BLOCK_REGEX)


=======

<<<<<<< main
FUNCTION_ID_BLOCK_REGEX = (
    r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
)
=======
FUNCTION_ID_BLOCK_REGEX = r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
>>>>>>> ms/small_fixes
>>>>>>> Stashed changes

FUNCTION_ID_BLOCK_MATCHER = compile(FUNCTION_ID_BLOCK_REGEX)


<<<<<<< Updated upstream
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
class FunctionIdBlock(Block):
    """Block to represent a function id. It can be used to call a function from a plugin.

    The content is parsed using a regex, that returns either a plugin and
    function name or just a function name, depending on the content.

<<<<<<< Updated upstream
    Anything other than that and a ValueError is raised.
=======
<<<<<<< main
    Anything other than that and a ValueError is raised.
=======
<<<<<<< main
    Anything other than that and a ValueError is raised.
=======
    Anything other then that and a ValueError is raised.
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes

    Args:
        content (str): The content of the block.
        function_name (Optional[str], optional): The function name.
        plugin_name (Optional[str], optional): The plugin name.

    Raises:
        ValueError: If the content does not have valid syntax.
    """

    type: ClassVar[BlockTypes] = BlockTypes.FUNCTION_ID
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
    function_name: str = ""
    plugin_name: str | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: dict[str, Any]) -> dict[str, Any]:
        """Parse the content of the function id block and extract the plugin and function name.

        If both are present in the fields, return the fields as is.
        Otherwise, use the regex to extract the plugin and function name.
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
=======
    function_name: Optional[str] = ""
    plugin_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the content of the function id block and extract the plugin and function name.

        If both are present in the fields, return the fields as is.
        Otherwise use the regex to extract the plugin and function name.
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
        """
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

<<<<<<< Updated upstream
    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
=======
<<<<<<< main
    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
=======
<<<<<<< main
    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
=======
    def render(self, *_: Tuple["Kernel", Optional["KernelArguments"]]) -> str:
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
        return self.content
