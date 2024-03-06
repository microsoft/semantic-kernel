from __future__ import annotations

from typing import Callable, List, Optional

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel


class PlannerOptions(KernelBaseModel):
    """The default planner options that planners inherit from"""

    excluded_plugins: set[str] = set()
    excluded_functions: set[str] = set()
    get_available_functions: Optional[Callable[["PlannerOptions", Optional[str]], List[KernelFunctionMetadata]]] = None
    # TODO semantic_memory_config
