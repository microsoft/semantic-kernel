# Copyright (c) Microsoft. All rights reserved.

import logging
from copy import copy
from typing import TYPE_CHECKING, Any, ClassVar, List, Optional, Tuple

from pydantic import Field

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

VALID_ARG_TYPES = [BlockTypes.VALUE, BlockTypes.VARIABLE, BlockTypes.NAMED_ARG]


class CodeBlock(Block):
    type: ClassVar[BlockTypes] = BlockTypes.CODE
    tokens: List[Block] = Field(default_factory=list)
    validated: bool = Field(False, init=False, exclude=True)

    def model_post_init(self, __context: Any):
        if not self.tokens:
            self.tokens = CodeTokenizer.tokenize(self.content)

    def is_valid(self) -> Tuple[bool, str]:
        error_msg = ""

        for token in self.tokens:
            is_valid, error_msg = token.is_valid()
            if not is_valid:
                logger.error(error_msg)
                return False, error_msg

        if len(self.tokens) > 1:
            if self.tokens[0].type != BlockTypes.FUNCTION_ID:
                error_msg = f"Unexpected first token found: {self.tokens[1].content}"
                logger.error(error_msg)
                return False, error_msg

            for index, token in enumerate(self.tokens[1:], start=1):
                if index == 1 and token.type not in VALID_ARG_TYPES:
                    error_msg = f"Unexpected token found: {token}"
                    logger.error(error_msg)
                    return False, error_msg
                if index > 1 and token.type != BlockTypes.NAMED_ARG:
                    error_msg = (
                        f"Unexpected token found: {token}, after the first argument all tokens must be named_args."
                    )
                    logger.error(error_msg)
                    return False, error_msg

        self.validated = True

        return True, ""

    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        if not self.validated:
            is_valid, error = self.is_valid()
            if not is_valid:
                raise ValueError(error)

        logger.debug(f"Rendering code: `{self.content}`")
        if len(self.tokens) == 0:
            raise ValueError("No tokens to render.")

        if self.tokens[0].type == BlockTypes.FUNCTION_ID:
            return await self._render_function_call(kernel, arguments)
        if self.tokens[0].type in VALID_ARG_TYPES:
            return self.tokens[0].render(kernel, arguments)

        raise ValueError(f"Unexpected first token type: {self.tokens[0].type}")

    async def _render_function_call(self, kernel: "Kernel", arguments: "KernelArguments"):
        if not kernel.plugins:
            raise ValueError("Plugin collection not set")
        function_block = self.tokens[0]
        function = self._get_function_from_plugin_collection(kernel.plugins, function_block)
        if not function:
            error_msg = f"Function `{function_block.content}` not found"
            logger.error(error_msg)
            raise ValueError(error_msg)

        arguments_clone = copy(arguments)
        if len(self.tokens) > 1:
            arguments_clone = self._enrich_function_arguments(kernel, arguments_clone, function.describe())

        result = await function.invoke(kernel, arguments_clone)
        if exc := result.metadata.get("error", None):
            raise ValueError("Function resulted in a error: %s", exc) from exc

        return str(result) if result else ""

    def _enrich_function_arguments(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments",
        function_metadata: KernelFunctionMetadata,
    ) -> "KernelArguments":
        if not function_metadata.parameters:
            raise ValueError(
                f"Function {function_metadata.plugin_name}.{function_metadata.name} does not take any arguments "
                f"but it is being called in the template with {len(self.tokens) - 1} arguments."
            )
        for index, token in enumerate(self.tokens[1:], start=1):
            logger.debug(f"Parsing variable/value: `{self.tokens[1].content}`")
            rendered_value = token.render(kernel, arguments)
            if token.type != BlockTypes.NAMED_ARG:
                if index == 1:
                    arguments[function_metadata.parameters[0].name] = rendered_value
                    continue
                error_msg = "Functions support up to one positional argument"
                logger.error(error_msg)
                raise AIException(AIException.ErrorCodes.InvalidPrompt, error_msg)
            arguments[token.name.name] = rendered_value

        return arguments

    def _get_function_from_plugin_collection(
        self, plugins: KernelPluginCollection, function_block: FunctionIdBlock
    ) -> Optional[KernelFunction]:
        """
        Get the function from the plugin collection

        Args:
            plugins: The plugin collection
            function_block: The function block that contains the function name

        Returns:
            The function if it exists, None otherwise.
        """
        if function_block.plugin_name is not None and len(function_block.plugin_name) > 0:
            return plugins[function_block.plugin_name][function_block.function_name]
        else:
            # We now require a plug-in name, but if one isn't set then we'll try to find the function
            for plugin in plugins:
                if function_block.function_name in plugin:
                    return plugin[function_block.function_name]

        return None
