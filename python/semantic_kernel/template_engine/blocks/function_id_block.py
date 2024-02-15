# Copyright (c) Microsoft. All rights reserved.

import logging
from re import match as re_match
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Tuple

from pydantic import Field

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.utils.validation import FULLY_QUALIFIED_FUNCTION_NAME, FUNCTION_NAME_REGEX

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class FunctionIdBlock(Block):
    type: ClassVar[BlockTypes] = BlockTypes.FUNCTION_ID
    plugin_name: Optional[str] = Field("", init=False, exclude=True)
    function_name: Optional[str] = Field("", init=False, exclude=True)
    validated: bool = Field(True, init=False, exclude=True)

    def model_post_init(self, __context: Any):
        if len(self.content) == 0:
            self.validated = False
            return
        if self.content.count(".") > 1:
            raise ValueError("The content should not have more then 1 dot in it.")
        names = re_match(FULLY_QUALIFIED_FUNCTION_NAME, self.content)
        if names and (groups := names.groupdict()):
            self.plugin_name = groups["plugin"]
            self.function_name = groups["function"]
            return
        if self.content[0] == ".":
            self.content = self.content[1:]
        function_only = re_match(FUNCTION_NAME_REGEX, self.content)
        if function_only:
            self.plugin_name = ""
            self.function_name = self.content
            return
        self.validated = False

    def is_valid(self) -> Tuple[bool, str]:
        if self.validated:
            return self.validated, ""
        return self.validated, "Not a valid plugin and function name, should be one dot surrounded by the names."

    def render(self, *_: Tuple["Kernel", Optional["KernelArguments"]]) -> str:
        return self.content
