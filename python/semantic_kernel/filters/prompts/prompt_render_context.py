# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.filters.filter_context_base import FilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.functions.function_result import FunctionResult


class PromptRenderContext(FilterContextBase):
    """Context for prompt rendering filters.

    When prompt rendering is expensive (for instance when there are expensive functions being called.)
    This filter can be used to set the rendered_prompt directly and returning.

    Attributes:
        function: The function invoked.
        kernel: The kernel used.
        arguments: The arguments used to call the function.
        rendered_prompt: The result of the prompt rendering.
        function_result: The result of the function that used the prompt.

    """

    rendered_prompt: str | None = None
    function_result: "FunctionResult | None" = None
