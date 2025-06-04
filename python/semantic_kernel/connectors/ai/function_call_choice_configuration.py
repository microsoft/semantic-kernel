# Copyright (c) Microsoft. All rights reserved.


from pydantic.dataclasses import dataclass

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
@dataclass
class FunctionCallChoiceConfiguration:
    """Configuration for function call choice."""

    available_functions: list[KernelFunctionMetadata] | None = None
