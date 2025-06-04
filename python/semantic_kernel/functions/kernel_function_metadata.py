# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.const import DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import FUNCTION_NAME_REGEX, PLUGIN_NAME_REGEX


class KernelFunctionMetadata(KernelBaseModel):
    """The kernel function metadata."""

    name: str = Field(..., pattern=FUNCTION_NAME_REGEX)
    plugin_name: str | None = Field(default=None, pattern=PLUGIN_NAME_REGEX)
    description: str | None = Field(default=None)
    parameters: list[KernelParameterMetadata] = Field(default_factory=list)
    is_prompt: bool
    is_asynchronous: bool | None = Field(default=True)
    return_parameter: KernelParameterMetadata | None = None
    additional_properties: dict[str, Any] | None = Field(default=None)

    @property
    def fully_qualified_name(self) -> str:
        """Get the fully qualified name of the function.

        A fully qualified name is the name of the combination of the plugin name and
        the function name, separated by a hyphen, if the plugin name is present.
        Otherwise, it is just the function name.

        Returns:
            The fully qualified name of the function.
        """
        return self.custom_fully_qualified_name(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR)

    def custom_fully_qualified_name(self, separator: str) -> str:
        """Get the fully qualified name of the function with a custom separator.

        Args:
            separator (str): The custom separator.

        Returns:
            The fully qualified name of the function with a custom separator.
        """
        return f"{self.plugin_name}{separator}{self.name}" if self.plugin_name else self.name

    def __eq__(self, other: object) -> bool:
        """Compare to another KernelFunctionMetadata instance.

        Args:
            other (KernelFunctionMetadata): The other KernelFunctionMetadata instance.

        Returns:
            True if the two instances are equal, False otherwise.
        """
        if not isinstance(other, KernelFunctionMetadata):
            return False

        return (
            self.name == other.name
            and self.plugin_name == other.plugin_name
            and self.description == other.description
            and self.parameters == other.parameters
            and self.is_prompt == other.is_prompt
            and self.is_asynchronous == other.is_asynchronous
            and self.return_parameter == other.return_parameter
        )
