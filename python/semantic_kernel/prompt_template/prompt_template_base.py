# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from html import escape
from typing import TYPE_CHECKING, Any

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel


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
        For string arguments, applies HTML encoding. For complex types, throws an exception unless
        allow_dangerously_set_content is set to true.

        Args:
            arguments: The kernel arguments
        """
        if self.allow_dangerously_set_content:
            return arguments

        from semantic_kernel.functions.kernel_arguments import KernelArguments

        new_args = KernelArguments(settings=arguments.execution_settings)
        for name, value in arguments.items():
            new_args[name] = self._get_encoded_value_or_default(name, value)
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

    def _get_encoded_value_or_default(self, name: str, value: Any) -> Any:
        """Encode argument value if necessary, or throw an exception if encoding is not supported.

        Args:
            name: The name of the property/argument.
            value: The value of the property/argument.

        Returns:
            The encoded value or the original value if encoding is not needed.

        Raises:
            NotImplementedError: If the value is a complex type and allow_dangerously_set_content is False.
        """
        if self.allow_dangerously_set_content:
            return value

        # Check if this variable allows dangerous content
        for variable in self.prompt_template_config.input_variables:
            if variable.name == name and variable.allow_dangerously_set_content:
                return value

        if isinstance(value, str):
            return escape(value)

        if self._is_safe_type(value):
            return value

        # For complex types, throw an exception if dangerous content is not allowed
        raise NotImplementedError(
            f"Argument '{name}' has a value that doesn't support automatic encoding. "
            f"Set allow_dangerously_set_content to 'True' for this argument and implement custom encoding, "
            "or provide the value as a string."
        )

    def _is_safe_type(self, value: Any) -> bool:
        """Determine if a type is considered safe and doesn't require encoding.

        Args:
            value: The value to check.

        Returns:
            True if the type is safe, False otherwise.
        """
        from datetime import datetime, timedelta
        from enum import Enum
        from uuid import UUID

        # Check for primitive types
        if isinstance(value, (int, float, bool, bytes)):
            return True

        # Check for date/time types
        if isinstance(value, (datetime, timedelta)):
            return True

        # Check for UUID
        if isinstance(value, UUID):
            return True

        # Check for enums
        if isinstance(value, Enum):
            return True

        # Check for None
        return value is None
