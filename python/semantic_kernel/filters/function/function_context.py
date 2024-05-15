# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.filters.kernel_filter_context_base import KernelFilterContextBase
from semantic_kernel.functions.function_result import FunctionResult


class FunctionContext(KernelFilterContextBase):
    """Base class for Function Hook Contexts."""

    result: FunctionResult | None = None
    exception: Exception | None = None
