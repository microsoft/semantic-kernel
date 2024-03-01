from __future__ import annotations
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

from typing import Any, Callable, List, Optional


class PlannerOptions(KernelBaseModel):
    excluded_plugins: set[str] = set()
    exclused_functions: set[str] = set()
    get_available_functions: Optional[Callable[["PlannerOptions", Optional[str]], List[KernelFunctionMetadata]]] = None
    # TODO semantic_memory_config
