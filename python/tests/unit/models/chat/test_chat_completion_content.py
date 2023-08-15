from semantic_kernel.models.chat.chat_completion_content import ChatCompletionContent
from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.finish_reason import FinishReasonEnum


def test_chat_completion_content():
    # Test initialization with custom values
    content = "Hello world!"
    message = ChatMessage(
        role="user",
        fixed_content=content,
    )
    chat_completion_content = ChatCompletionContent(
        index=0, message=message, finish_reason="stop"
    )

    assert chat_completion_content.index == 0
    assert chat_completion_content.finish_reason is FinishReasonEnum.stop
    assert chat_completion_content.message.content == content
