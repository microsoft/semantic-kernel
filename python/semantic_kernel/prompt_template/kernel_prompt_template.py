# Copyright (c) Microsoft. All rights reserved.

import logging
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
from html import escape
from typing import TYPE_CHECKING, Any

from pydantic import PrivateAttr, field_validator

from semantic_kernel.exceptions import TemplateRenderException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.named_arg_block import NamedArgBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import PrivateAttr

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.protocols.text_renderer import TextRenderer
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
from semantic_kernel.template_engine.template_tokenizer import TemplateTokenizer

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
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
<<<<<<< Updated upstream
>>>>>>> Stashed changes
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )
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
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )
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
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )
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

logger: logging.Logger = logging.getLogger(__name__)


class KernelPromptTemplate(PromptTemplateBase):
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
    """Create a Kernel prompt template."""

    _blocks: list[Block] = PrivateAttr(default_factory=list)

    @field_validator("prompt_template_config")
    @classmethod
    def validate_template_format(
        cls, v: "PromptTemplateConfig"
    ) -> "PromptTemplateConfig":
        """Validate the template format."""
        if v.template_format != KERNEL_TEMPLATE_FORMAT_NAME:
            raise ValueError(
                f"Invalid prompt template format: {v.template_format}. Expected: semantic-kernel"
            )
        return v

    def model_post_init(self, _: Any) -> None:
        """Post init model."""
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
>>>>>>> Stashed changes
=======
=======
=======
=======
>>>>>>> Stashed changes
    prompt_template_config: PromptTemplateConfig
    _blocks: List[Block] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
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
        self._blocks = self.extract_blocks()
        # Add all of the existing input variables to our known set. We'll avoid adding any
        # dynamically discovered input variables with the same name.
        seen = {iv.name.lower() for iv in self.prompt_template_config.input_variables}

        # Enumerate every block in the template, adding any variables that are referenced.
        for block in self._blocks:
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
            if isinstance(block, VarBlock):
                # Add all variables from variable blocks, e.g. "{{$a}}".
                self._add_if_missing(block.name, seen)
                continue
            if isinstance(block, CodeBlock):
                for sub_block in block.tokens:
                    if isinstance(sub_block, VarBlock):
                        # Add all variables from code blocks, e.g. "{{p.bar $b}}".
                        self._add_if_missing(sub_block.name, seen)
                        continue
                    if isinstance(sub_block, NamedArgBlock) and sub_block.variable:
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
            if block.type == BlockTypes.VARIABLE:
                # Add all variables from variable blocks, e.g. "{{$a}}".
                self._add_if_missing(block.name, seen)
                continue
            if block.type == BlockTypes.CODE:
                for sub_block in block.tokens:
                    if sub_block.type == BlockTypes.VARIABLE:
                        # Add all variables from code blocks, e.g. "{{p.bar $b}}".
                        self._add_if_missing(sub_block.name, seen)
                        continue
                    if sub_block.type == BlockTypes.NAMED_ARG and sub_block.variable:
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
                        # Add all variables from named arguments, e.g. "{{p.bar b = $b}}".
                        # represents a named argument for a function call.
                        # For example, in the template {{ MyPlugin.MyFunction var1=$boo }}, var1=$boo
                        # is a named arg block.
                        self._add_if_missing(sub_block.variable.name, seen)

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
    def extract_blocks(self) -> list[Block]:
        """Given the prompt template, extract all the blocks (text, variables, function calls)."""
        logger.debug(
            f"Extracting blocks from template: {self.prompt_template_config.template}"
        )
        if not self.prompt_template_config.template:
            return []
        return TemplateTokenizer.tokenize(self.prompt_template_config.template)

    def _add_if_missing(self, variable_name: str, seen: set):
        # Convert variable_name to lower case to handle case-insensitivity
        if variable_name and variable_name.lower() not in seen:
            seen.add(variable_name.lower())
            self.prompt_template_config.input_variables.append(
                InputVariable(name=variable_name)
            )

    async def render(
        self, kernel: "Kernel", arguments: "KernelArguments | None" = None
    ) -> str:
        """Render the prompt template.

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
    def _add_if_missing(self, variable_name: str, seen: Optional[set] = None):
        # Convert variable_name to lower case to handle case-insensitivity
        if variable_name and variable_name.lower() not in seen:
            seen.add(variable_name.lower())
            self.prompt_template_config.input_variables.append(InputVariable(name=variable_name))

    def extract_blocks(self) -> List[Block]:
        """
        Given a prompt template string, extract all the blocks
        (text, variables, function calls).

        Args:
            template_text: Prompt template

        Returns:
            A list of all the blocks, ie the template tokenized in
            text, variables and function calls
        """
        logger.debug(f"Extracting blocks from template: {self.prompt_template_config.template}")
        if not self.prompt_template_config.template:
            return []
        return TemplateTokenizer.tokenize(self.prompt_template_config.template)

    async def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> str:
        """
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
        Using the prompt template, replace the variables with their values
        and execute the functions replacing their reference with the
        function result.

        Args:
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
            kernel ("Kernel"): The kernel to use for functions.
            arguments ("KernelArguments | None"): The arguments to use for rendering. (Default value = None)

        Returns:
            str: The prompt template ready to be used for an AI request

        """
        return await self.render_blocks(self._blocks, kernel, arguments)

    async def render_blocks(
        self,
        blocks: list[Block],
        kernel: "Kernel",
        arguments: "KernelArguments | None" = None,
    ) -> str:
        """Given a list of blocks render each block and compose the final result.

        Args:
            blocks (list[Block]): Template blocks generated by ExtractBlocks
            kernel ("Kernel"): The kernel to use for functions
            arguments ("KernelArguments | None"): The arguments to use for rendering (Default value = None)

        Returns:
            str: The prompt template ready to be used for an AI request

        """
        from semantic_kernel.template_engine.protocols.code_renderer import CodeRenderer
        from semantic_kernel.template_engine.protocols.text_renderer import TextRenderer

        logger.debug(f"Rendering list of {len(blocks)} blocks")
        rendered_blocks: list[str] = []
        arguments = self._get_trusted_arguments(arguments or KernelArguments())
        allow_unsafe_function_output = self._get_allow_dangerously_set_function_output()
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
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
            kernel: The kernel instance
            arguments: The kernel arguments

        Returns:
            The prompt template ready to be used for an AI request
        """
        if not arguments:
            arguments = KernelArguments()
        return await self.render_blocks(self._blocks, kernel, arguments)

    async def render_blocks(self, blocks: List[Block], kernel: "Kernel", arguments: "KernelArguments") -> str:
        """
        Given a list of blocks render each block and compose the final result.

        :param blocks: Template blocks generated by ExtractBlocks
        :param context: Access into the current kernel execution context
        :return: The prompt template ready to be used for an AI request
        """
        from semantic_kernel.template_engine.protocols.code_renderer import CodeRenderer

        logger.debug(f"Rendering list of {len(blocks)} blocks")
        rendered_blocks: List[str] = []
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
        for block in blocks:
            if isinstance(block, TextRenderer):
                rendered_blocks.append(block.render(kernel, arguments))
                continue
            if isinstance(block, CodeRenderer):
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
                try:
                    rendered = await block.render_code(kernel, arguments)
                except Exception as exc:
                    logger.error(f"Error rendering code block: {exc}")
                    raise TemplateRenderException(
                        f"Error rendering code block: {exc}"
                    ) from exc
                rendered_blocks.append(
                    rendered if allow_unsafe_function_output else escape(rendered)
                )
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        prompt = "".join(rendered_blocks)
        logger.debug(f"Rendered prompt: {prompt}")
        return prompt
=======
=======
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
<<<<<<< HEAD
        prompt = "".join(rendered_blocks)
        logger.debug(f"Rendered prompt: {prompt}")
        return prompt
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                rendered_blocks.append(await block.render_code(kernel, arguments))
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
        prompt = "".join(rendered_blocks)
        logger.debug(f"Rendered prompt: {prompt}")
        return prompt

<<<<<<< HEAD
    @staticmethod
    def quick_render(template: str, arguments: dict[str, Any]) -> str:
        """Quick render a Kernel prompt template, only supports text and variable blocks.

        Args:
            template: The template to render
            arguments: The arguments to use for rendering

        Returns:
            str: The prompt template ready to be used for an AI request

        """
        from semantic_kernel import Kernel
        from semantic_kernel.template_engine.protocols.code_renderer import CodeRenderer

        blocks = TemplateTokenizer.tokenize(template)
        if any(isinstance(block, CodeRenderer) for block in blocks):
            raise ValueError("Quick render does not support code blocks.")
        kernel = Kernel()
        return "".join([block.render(kernel, arguments) for block in blocks])
=======
    def render_variables(
        self, blocks: List[Block], kernel: "Kernel", arguments: Optional["KernelArguments"] = None
    ) -> List[Block]:
        """
        Given a list of blocks, render the Variable Blocks, replacing
        placeholders with the actual value in memory.

        :param blocks: List of blocks, typically all the blocks found in a template
        :param variables: Container of all the temporary variables known to the kernel
        :return: An updated list of blocks where Variable Blocks have rendered to
            Text Blocks
        """
        from semantic_kernel.template_engine.blocks.text_block import TextBlock

        logger.debug("Rendering variables")

        rendered_blocks: List[Block] = []
        for block in blocks:
            if block.type == BlockTypes.VARIABLE:
                rendered_blocks.append(TextBlock.from_text(block.render(kernel, arguments)))
                continue
            rendered_blocks.append(block)

        return rendered_blocks

    async def render_code(self, blocks: List[Block], kernel: "Kernel", arguments: "KernelArguments") -> List[Block]:
        """
        Given a list of blocks, render the Code Blocks, executing the
        functions and replacing placeholders with the functions result.

        :param blocks: List of blocks, typically all the blocks found in a template
        :param execution_context: Access into the current kernel execution context
        :return: An updated list of blocks where Code Blocks have rendered to
            Text Blocks
        """
        from semantic_kernel.template_engine.blocks.text_block import TextBlock

        logger.debug("Rendering code")

        rendered_blocks: List[Block] = []
        for block in blocks:
            if block.type == BlockTypes.CODE:
                rendered_blocks.append(TextBlock.from_text(await block.render_code(kernel, arguments)))
                continue
            rendered_blocks.append(block)

        return rendered_blocks
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
