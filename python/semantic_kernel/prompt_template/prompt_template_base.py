# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from urllib.parse import quote

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.input_variable import InputVariable


class PromptTemplateBase(KernelBaseModel, ABC):
    prompt_template_config: PromptTemplateConfig
    allow_unsafe_content: bool = False

    @abstractmethod
    async def render(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        pass

    def _get_checked_arguments(
        self,
        arguments: "KernelArguments",
        prompt_template_config: "PromptTemplateConfig",
    ):
        """
        Validate the arguments against the prompt template.

        Args:
            arguments: The kernel arguments
            allow_unsafe_content: Allow unsafe content in the prompt template
        """
        from semantic_kernel.functions.kernel_arguments import KernelArguments

        new_args = KernelArguments(settings=arguments.execution_settings)
        for name, value in arguments.items():
            if isinstance(value, str) and self._should_encode(name, prompt_template_config.input_variables):
                new_args[name] = quote(value)
            else:
                new_args[name] = value
        return new_args

    def _should_encode(self, name: str, input_variables: list["InputVariable"]) -> bool:
        """
        Check if the variable should be encoded.

        If the PromptTemplate allows unsafe content, then the variable will not be encoded,
        even if the input_variables does specify this.

        Otherwise, it checks the input_variables to see if the variable should be encoded.

        Otherwise, it will encode.

        Args:
            name: The variable name
            input_variables: The input variables
        """
        if self.allow_unsafe_content:
            return False
        for variable in input_variables:
            if variable.name == name:
                return not variable.allow_unsafe_content
        return True
