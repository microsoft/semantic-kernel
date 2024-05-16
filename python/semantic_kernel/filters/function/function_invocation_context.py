# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.filters.filter_context_base import FilterContextBase
from semantic_kernel.functions.function_result import FunctionResult


class FunctionInvocationContext(FilterContextBase):
    """Class for function invocation context."""

    result: FunctionResult | None = None
