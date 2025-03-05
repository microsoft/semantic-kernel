# Copyright (c) Microsoft. All rights reserved.


from pydantic.dataclasses import dataclass

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
@dataclass
class FunctionCallChoiceConfiguration:
    """Configuration for function call choice."""

    available_functions: list[KernelFunctionMetadata] | None = None
