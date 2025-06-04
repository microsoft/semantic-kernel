# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Callable

from pydantic import Field

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated


@deprecated("Will be removed in a future version.")
class PlannerOptions(KernelBaseModel):
    """The default planner options that planners inherit from."""

    excluded_plugins: set[str] = Field(default_factory=set)
    excluded_functions: set[str] = Field(default_factory=set)
    get_available_functions: Callable[["PlannerOptions", str | None], list[KernelFunctionMetadata]] | None = None
