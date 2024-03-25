# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from collections.abc import Callable

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel


class PlannerOptions(KernelBaseModel):
    """The default planner options that planners inherit from"""

    excluded_plugins: set[str] = set()
    excluded_functions: set[str] = set()
    get_available_functions: Callable[["PlannerOptions | str | None"], list[KernelFunctionMetadata]] | None = None
    # TODO semantic_memory_config
