# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.models.ai.chat_completion.chat_message import ChatMessage


def test_chat_message():
    # Test initialization with default values
    message = ChatMessage()
    assert message.role == "assistant"
    assert message.fixed_content is None
    assert message.content is None
    assert message.content_template is None
