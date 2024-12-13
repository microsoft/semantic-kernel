# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.filters.filter_context_base import FilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.functions.function_result import FunctionResult


class AutoFunctionInvocationContext(FilterContextBase):
    """Class for auto function invocation context.

    This is the context supplied to the auto function invocation filters.

    Common use case are to alter the function_result, for instance filling it with a pre-computed
    value, in order to skip a step, for instance when doing caching.

    Another option is to terminate, this can be done by setting terminate to True.

    Attributes:
        function: The function invoked.
        kernel: The kernel used.
        arguments: The arguments used to call the function.
        chat_history: The chat history or None.
        function_result: The function result or None.
        request_sequence_index: The request sequence index.
        function_sequence_index: The function sequence index.
        function_count: The function count.
        terminate: The flag to terminate.

    """

    chat_history: "ChatHistory | None" = None
    function_result: "FunctionResult | None" = None
    request_sequence_index: int = 0
    function_sequence_index: int = 0
    function_count: int = 0
    terminate: bool = False
