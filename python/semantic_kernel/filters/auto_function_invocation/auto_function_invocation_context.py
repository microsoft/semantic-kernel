# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.filters.filter_context_base import FilterContextBase

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.functions.function_result import FunctionResult


class AutoFunctionInvocationContext(FilterContextBase):
    """Class for auto function invocation context."""

    chat_history: "ChatHistory | None" = None
    function_result: "FunctionResult | None" = None
    request_sequence_index: int = 0
    function_sequence_index: int = 0
    function_count: int = 0
    terminate: bool = False
