# Copyright (c) Microsoft. All rights reserved.

import logging
from re import compile
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
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
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import model_validator

from semantic_kernel.exceptions import FunctionIdBlockSyntaxError
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< main
=======
=======
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Tuple

from pydantic import model_validator

>>>>>>> ms/small_fixes
>>>>>>> origin/main
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import FunctionIdBlockSyntaxError
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
=======
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Tuple

from pydantic import model_validator

>>>>>>> ms/small_fixes
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_errors import FunctionIdBlockSyntaxError
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
from semantic_kernel.template_engine.blocks.block_types import BlockTypes

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel
<<<<<<< Updated upstream
<<<<<<< head

logger: logging.Logger = logging.getLogger(__name__)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

FUNCTION_ID_BLOCK_REGEX = (
    r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
)
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

logger: logging.Logger = logging.getLogger(__name__)
>>>>>>> Stashed changes
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

FUNCTION_ID_BLOCK_MATCHER = compile(FUNCTION_ID_BLOCK_REGEX)


<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
class FunctionIdBlock(Block):
    """Block to represent a function id. It can be used to call a function from a plugin.

    The content is parsed using a regex, that returns either a plugin and
    function name or just a function name, depending on the content.

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    Anything other than that and a ValueError is raised.
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
<<<<<<< main
    Anything other than that and a ValueError is raised.
=======
<<<<<<< main
    Anything other than that and a ValueError is raised.
=======
    Anything other then that and a ValueError is raised.
>>>>>>> ms/small_fixes
>>>>>>> origin/main
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

    Args:
        content (str): The content of the block.
        function_name (Optional[str], optional): The function name.
        plugin_name (Optional[str], optional): The plugin name.

    Raises:
        ValueError: If the content does not have valid syntax.
    """

    type: ClassVar[BlockTypes] = BlockTypes.FUNCTION_ID
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
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
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
    function_name: str = ""
    plugin_name: str | None = None

=======

logger: logging.Logger = logging.getLogger(__name__)

<<<<<<< main
FUNCTION_ID_BLOCK_REGEX = (
    r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
)
=======
FUNCTION_ID_BLOCK_REGEX = r"^((?P<plugin>[0-9A-Za-z_]+)[.])?(?P<function>[0-9A-Za-z_]+)$"
>>>>>>> ms/small_fixes

FUNCTION_ID_BLOCK_MATCHER = compile(FUNCTION_ID_BLOCK_REGEX)


class FunctionIdBlock(Block):
    """Block to represent a function id. It can be used to call a function from a plugin.

    The content is parsed using a regex, that returns either a plugin and
    function name or just a function name, depending on the content.

<<<<<<< main
    Anything other than that and a ValueError is raised.
=======
    Anything other then that and a ValueError is raised.
>>>>>>> ms/small_fixes

    Args:
        content (str): The content of the block.
        function_name (Optional[str], optional): The function name.
        plugin_name (Optional[str], optional): The plugin name.

    Raises:
        ValueError: If the content does not have valid syntax.
    """

    type: ClassVar[BlockTypes] = BlockTypes.FUNCTION_ID
<<<<<<< main
    function_name: str = ""
    plugin_name: str | None = None

>>>>>>> origin/main
=======
    function_name: str = ""
    plugin_name: str | None = None

>>>>>>> Stashed changes
    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: dict[str, Any]) -> dict[str, Any]:
        """Parse the content of the function id block and extract the plugin and function name.

        If both are present in the fields, return the fields as is.
        Otherwise, use the regex to extract the plugin and function name.
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    function_name: Optional[str] = ""
    plugin_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def parse_content(cls, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the content of the function id block and extract the plugin and function name.

        If both are present in the fields, return the fields as is.
        Otherwise use the regex to extract the plugin and function name.
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
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
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
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
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
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
<<<<<<< main
    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
    def render(self, *_: "Kernel | KernelArguments | None") -> str:
        """Render the function id block."""
=======
    def render(self, *_: Tuple["Kernel", Optional["KernelArguments"]]) -> str:
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
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
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        return self.content
