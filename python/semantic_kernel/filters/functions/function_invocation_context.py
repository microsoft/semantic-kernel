# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.filters.filter_context_base import FilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.functions.function_result import FunctionResult


class FunctionInvocationContext(FilterContextBase):
    """Class for function invocation context.

    This filter can be used to monitor which functions are called.
    To log what function was called with which parameters and what output.
    Finally it can be used for caching by setting the result value.

    Attributes:
        function: The function invoked.
        kernel: The kernel used.
        arguments: The arguments used to call the function.
        result: The result of the function, or None.

    """

    result: "FunctionResult | None" = None
