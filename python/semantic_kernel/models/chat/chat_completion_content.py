"""Class to hold chat completion content."""

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.completion_content_base import CompletionContentBase


class ChatCompletionContent(CompletionContentBase):
    message: ChatMessage


class ChatCompletionChunkContent(CompletionContentBase):
    delta: ChatMessage
