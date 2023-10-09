"""Class to hold chat messages."""
from typing import Optional

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import (
    FunctionCall,
)
from semantic_kernel.models.chat.chat_message import ChatMessage


class OpenAIChatMessage(ChatMessage):
    """Class to hold openai chat messages, which might include name and function_call fields."""

    name: Optional[str] = None
    function_call: Optional[FunctionCall] = None
