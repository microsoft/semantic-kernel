# Copyright (c) Microsoft. All rights reserved.

import logging
from copy import copy
from typing import TYPE_CHECKING, List, Optional, Tuple

from pydantic import Field

from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class CodeBlock(Block):
    tokens: List[Block] = Field(default_factory=list)
    validated: bool = False

    def __init__(
        self,
        content: str,
        tokens: Optional[List[Block]] = None,
    ):
        super().__init__(content=content and content.strip())
        self.tokens = tokens or CodeTokenizer.tokenize(content)

    @property
    def type(self) -> BlockTypes:
        return BlockTypes.CODE

    def is_valid(self) -> Tuple[bool, str]:
        error_msg = ""

        for token in self.tokens:
            is_valid, error_msg = token.is_valid()
            if not is_valid:
                logger.error(error_msg)
                return False, error_msg

        if len(self.tokens) > 1:
            if self.tokens[0].type != BlockTypes.FUNCTION_ID:
                error_msg = f"Unexpected second token found: {self.tokens[1].content}"
                logger.error(error_msg)
                return False, error_msg

            if self.tokens[1].type != BlockTypes.VALUE and self.tokens[1].type != BlockTypes.VARIABLE:
                error_msg = "Functions support only one parameter"
                logger.error(error_msg)
                return False, error_msg

        if len(self.tokens) > 2:
            error_msg = f"Unexpected second token found: {self.tokens[1].content}"
            logger.error(error_msg)
            return False, error_msg

        self.validated = True

        return True, ""

    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments"):
        if not self.validated:
            is_valid, error = self.is_valid()
            if not is_valid:
                raise ValueError(error)

        logger.debug(f"Rendering code: `{self.content}`")

        if self.tokens[0].type in (BlockTypes.VALUE, BlockTypes.VARIABLE):
            return self.tokens[0].render(kernel, arguments)

        if self.tokens[0].type == BlockTypes.FUNCTION_ID:
            return await self._render_function_call(self.tokens[0], kernel, arguments)

        raise ValueError(f"Unexpected first token type: {self.tokens[0].type}")

    async def _render_function_call(self, f_block: FunctionIdBlock, kernel: "Kernel", arguments: "KernelArguments"):
        if not kernel.plugins:
            raise ValueError("Plugin collection not set")

        function = self._get_function_from_plugin_collection(kernel.plugins, f_block)

        if not function:
            error_msg = f"Function `{f_block.content}` not found"
            logger.error(error_msg)
            raise ValueError(error_msg)

        arguments_clone = copy(arguments)

        if len(self.tokens) > 1:
            logger.debug(f"Passing variable/value: `{self.tokens[1].content}`")
            input_value = self.tokens[1].render(kernel, arguments_clone)
            arg_name = self.tokens[1].content
            if arg_name and arg_name.startswith("$"):
                arg_name = arg_name[1:]
            arguments_clone[arg_name] = input_value

        result = await function.invoke(kernel, arguments_clone)
        return str(result) if result else ""

    def _get_function_from_plugin_collection(
        self, plugins: KernelPluginCollection, f_block: FunctionIdBlock
    ) -> Optional[KernelFunction]:
        """
        Get the function from the plugin collection

        Args:
            plugins: The plugin collection
            f_block: The function block that contains the function name

        Returns:
            The function if it exists, None otherwise.
        """
        if f_block.plugin_name is not None and len(f_block.plugin_name) > 0:
            return plugins[f_block.plugin_name][f_block.function_name]
        else:
            # We now require a plug-in name, but if one isn't set then we'll try to find the function
            for plugin in plugins:
                if f_block.function_name in plugin:
                    return plugin[f_block.function_name]

        return None
