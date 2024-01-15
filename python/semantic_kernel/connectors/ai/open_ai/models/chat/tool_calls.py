"""Class to hold chat messages."""
from typing import Literal, Optional

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.sk_pydantic import SKBaseModel


class ToolCall(SKBaseModel):
    """Class to hold a tool call response."""

    id: Optional[str] = None
    type: Optional[Literal["function"]] = "function"
    function: Optional[FunctionCall] = None

    def update(self, chunk: "ToolCall"):
        """Update the function call."""
        if self.function:
            self.function.update(chunk.function.name, chunk.function.arguments)
