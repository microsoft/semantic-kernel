# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional

from pydantic import Field

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import FUNCTION_NAME_REGEX, PLUGIN_NAME_REGEX


class KernelFunctionMetadata(KernelBaseModel):
    name: str = Field(pattern=FUNCTION_NAME_REGEX)
    plugin_name: Optional[str] = Field(None, pattern=PLUGIN_NAME_REGEX)
    description: Optional[str] = Field(default=None)
    parameters: List[KernelParameterMetadata] = Field(default_factory=list)
    is_prompt: bool
    is_asynchronous: Optional[bool] = Field(default=True)
    return_parameter: Optional[KernelParameterMetadata] = None

    @property
    def fully_qualified_name(self) -> str:
        """
        Get the fully qualified name of the function.

        Returns:
            The fully qualified name of the function.
        """
        return f"{self.plugin_name}-{self.name}" if self.plugin_name else self.name

    def __eq__(self, other: object) -> bool:
        """
        Compare to another KernelFunctionMetadata instance.

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
