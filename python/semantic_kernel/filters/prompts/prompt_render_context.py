# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.filters.filter_context_base import FilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.functions.function_result import FunctionResult


class PromptRenderContext(FilterContextBase):
    """Context for prompt rendering filters."""

    rendered_prompt: str | None = None
    function_result: "FunctionResult | None" = None
