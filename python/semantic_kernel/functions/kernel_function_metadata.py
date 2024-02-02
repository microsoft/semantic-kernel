# Copyright (c) Microsoft. All rights reserved.

from typing import List

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import validate_function_name


class KernelFunctionMetadata(KernelBaseModel):
    name: str
    plugin_name: str
    description: str
    is_semantic: bool
    parameters: List[KernelParameterMetadata]
    is_asynchronous: bool = True

    def __init__(
        self,
        name: str,
        plugin_name: str,
        description: str,
        parameters: List[KernelParameterMetadata],
        is_semantic: bool,
        is_asynchronous: bool = True,
    ) -> None:
        validate_function_name(name)
        super().__init__(
            name=name,
            plugin_name=plugin_name,
            description=description,
            parameters=parameters,
            is_semantic=is_semantic,
            is_asynchronous=is_asynchronous,
        )

    def __eq__(self, other):
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
            and self.is_semantic == other.is_semantic
            and self.is_asynchronous == other.is_asynchronous
        )
