# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import Sequence
from html import escape
from typing import TYPE_CHECKING

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.input_variable import InputVariable


class PromptTemplateBase(KernelBaseModel, ABC):
    """Base class for prompt templates."""

    prompt_template_config: PromptTemplateConfig
    allow_dangerously_set_content: bool = False

    @abstractmethod
    async def render(self, kernel: "Kernel", arguments: "KernelArguments | None" = None) -> str:
        """Render the prompt template."""
        pass

    def _get_trusted_arguments(
        self,
        arguments: "KernelArguments",
    ) -> "KernelArguments":
        """Get the trusted arguments.

        If the prompt template allows unsafe content, then we do not encode the arguments.
        Otherwise, each argument is checked against the input variables to see if it allowed to be unencoded.
        Only works on string variables.

        Args:
            arguments: The kernel arguments
        """
        if self.allow_dangerously_set_content:
            return arguments

        from semantic_kernel.functions.kernel_arguments import KernelArguments

        new_args = KernelArguments(settings=arguments.execution_settings)
        for name, value in arguments.items():
            if isinstance(value, str) and self._should_escape(name, self.prompt_template_config.input_variables):
                new_args[name] = escape(value)
            else:
                new_args[name] = value
        return new_args

    def _get_allow_dangerously_set_function_output(self) -> bool:
        """Get the allow_dangerously_set_content flag.

        If the prompt template allows unsafe content, then we do not encode the function output,
        unless explicitly allowed by the prompt template config

        """
        allow_dangerously_set_content = self.allow_dangerously_set_content
        if self.prompt_template_config.allow_dangerously_set_content:
            allow_dangerously_set_content = True
        return allow_dangerously_set_content

    def _should_escape(self, name: str, input_variables: Sequence["InputVariable"]) -> bool:
        """Check if the variable should be escaped.

        If the PromptTemplate allows dangerously set content, then the variable will not be escaped,
        even if the input_variables does specify this.

        Otherwise, it checks the input_variables to see if the variable should be encoded.

        Otherwise, it will encode.

        Args:
            name: The variable name
            input_variables: The input variables
        """
        for variable in input_variables:
            if variable.name == name:
                return not variable.allow_dangerously_set_content
        return True
