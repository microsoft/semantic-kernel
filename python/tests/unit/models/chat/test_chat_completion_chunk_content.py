from semantic_kernel.models.chat.chat_completion_content import (
    ChatCompletionChunkContent,
)
from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.finish_reason import FinishReasonEnum


def test_chat_completion_chunk_content():
    # Test initialization with custom values
    content = "Hello, world!"
    message = ChatMessage(
        role="user",
        fixed_content=content,
    )
    chat_completion_chunk_content = ChatCompletionChunkContent(
        index=0, delta=message, finish_reason="stop"
    )

    assert chat_completion_chunk_content.index == 0
    assert chat_completion_chunk_content.finish_reason is FinishReasonEnum.stop
    assert chat_completion_chunk_content.delta.content == content
