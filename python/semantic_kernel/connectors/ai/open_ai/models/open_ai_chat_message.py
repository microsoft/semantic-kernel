"""Class to hold chat messages."""
from typing import Optional

from openai.openai_object import OpenAIObject

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.chat.role import Role


class OpenAIChatMessage(ChatMessage):
    """Open AI API specific chat message constructors and methods."""

    @classmethod
    def from_openai_object(cls, openai_object: OpenAIObject) -> "ChatMessage":
        """Parse a OpenAI Object response into a ChatMessage."""
        return cls(
            role=Role(openai_object.role) if hasattr(openai_object, "role") else None,
            fixed_content=openai_object.content
            if hasattr(openai_object, "content")
            else None,
            name=openai_object.name if hasattr(openai_object, "name") else None,
        )

    def add_openai_chunk(self, openai_object: OpenAIObject) -> Optional["ChatMessage"]:
        """Parse a OpenAI Object response into a ChatMessage."""
        if self.fixed_content is None:
            self.fixed_content = ""
        if hasattr(openai_object, "delta"):
            self.fixed_content += openai_object.delta.content

        return self
