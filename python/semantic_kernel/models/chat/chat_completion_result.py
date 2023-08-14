"""Class to hold chat messages."""
from typing import List, Optional

from semantic_kernel.models.chat.chat_completion_content import (
    ChatCompletionContent,
)
from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.chat.role import Role
from semantic_kernel.models.completion_result_base import CompletionResultBase


class ChatCompletionResult(CompletionResultBase):
    """Class to hold chat completion results."""

    @property
    def chat_message(self) -> Optional[ChatMessage]:
        """Return the first message returned by the API."""
        if self.choices:
            return (
                self.choices[0].delta
                if self.is_streaming_result
                else self.choices[0].message
            )
        return None

    @property
    def content(self) -> Optional[str]:
        """Return the content of the first choice returned by the API."""
        if self.chat_message:
            return self.chat_message.fixed_content
        return None

    @classmethod
    def from_chunk_list(
        cls, chunk_list: List["ChatCompletionResult"]
    ) -> "ChatCompletionResult":
        """Parse a list of ChatCompletionResults with ChunkContent into a ChatCompletionResult."""
        completion_id = chunk_list[0].id
        created = chunk_list[0].created
        object_type = "chat.completion"
        model = chunk_list[0].model
        usage = None
        choices = {}
        for chunk in chunk_list:
            usage = chunk.usage if chunk.usage else usage
            completion_id = chunk.id if chunk.id else completion_id
            created = chunk.created if chunk.created else created
            model = chunk.model if chunk.model else model
            for choice in chunk.choices:
                if choice.index in choices:
                    if choice.finish_reason:
                        choices[choice.index].finish_reason = choice.finish_reason
                    if choice.delta.role:
                        choices[choice.index].message.role = choice.delta.role
                    if choice.delta.content:
                        choices[
                            choice.index
                        ].message.fixed_content += choice.delta.content
                else:
                    choices[choice.index] = ChatCompletionContent(
                        index=choice.index,
                        message=ChatMessage(
                            role=Role.assistant,
                            fixed_content=choice.delta.content or "",
                            name=choice.delta.name,
                        ),
                        finish_reason=choice.finish_reason,
                    )
        return cls(
            id=completion_id,
            object_type=object_type,
            created=created,
            model=model,
            choices=list(choices.values()),
            usage=usage,
            is_streaming_result=False,
        )
