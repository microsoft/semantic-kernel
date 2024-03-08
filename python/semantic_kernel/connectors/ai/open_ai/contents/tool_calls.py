# Copyright (c) Microsoft. All rights reserved.
from typing import Literal, Optional

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.kernel_pydantic import KernelBaseModel


class ToolCall(KernelBaseModel):
    """Class to hold a tool call response."""

    id: Optional[str] = None
    type: Optional[Literal["function"]] = "function"
    function: Optional[FunctionCall] = None

    def __add__(self, other: Optional["ToolCall"]) -> "ToolCall":
        """Add two tool calls together, combines the function calls, ignores the id."""
        if not other:
            return self
        return ToolCall(
            id=self.id or other.id,
            type=self.type or other.type,
            function=self.function + other.function if self.function else other.function,
        )
