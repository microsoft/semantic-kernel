"""Class to hold chat messages."""
from typing import Optional

from semantic_kernel.connectors.ai.open_ai.models.chat_completion.function_call import (
    FunctionCall,
)
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.tool_calls import ToolCall
from semantic_kernel.models.ai.chat_completion.chat_message import ChatMessage


class OpenAIChatMessage(ChatMessage):
    """Class to hold openai chat messages, which might include name, function_call and tool_calls fields."""

    name: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    tool_calls: Optional[ToolCall] = None
    tool_call_id: Optional[str] = None
