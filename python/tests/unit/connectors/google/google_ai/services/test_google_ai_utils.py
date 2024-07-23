# Copyright (c) Microsoft. All rights reserved.

from google.generativeai.protos import Candidate, Part

from semantic_kernel.connectors.ai.google.google_ai.services.utils import (
    filter_first_system_message,
    finish_reason_from_google_ai_to_semantic_kernel,
    format_user_message,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason


def test_finish_reason_from_google_ai_to_semantic_kernel():
    """Test finish_reason_from_google_ai_to_semantic_kernel."""
    assert finish_reason_from_google_ai_to_semantic_kernel(Candidate.FinishReason.STOP) == FinishReason.STOP
    assert finish_reason_from_google_ai_to_semantic_kernel(Candidate.FinishReason.MAX_TOKENS) == FinishReason.LENGTH
    assert finish_reason_from_google_ai_to_semantic_kernel(Candidate.FinishReason.SAFETY) == FinishReason.CONTENT_FILTER
    assert finish_reason_from_google_ai_to_semantic_kernel(Candidate.FinishReason.OTHER) is None


def test_filter_first_system_message():
    """Test filter_first_system_message."""
    chat_history = ChatHistory()
    chat_history.add_system_message("System message")
    chat_history.add_user_message("User message")
    assert filter_first_system_message(chat_history) == "System message"

    chat_history = ChatHistory()
    chat_history.add_user_message("User message")
    assert filter_first_system_message(chat_history) is None


def test_format_user_message():
    """Test format_user_message."""
    user_message = ChatMessageContent(role=AuthorRole.USER, content="User message")
    formatted_user_message = format_user_message(user_message)

    assert len(formatted_user_message) == 1
    assert isinstance(formatted_user_message[0], Part)
    assert formatted_user_message[0].text == "User message"

    # Test with an image content
    image_content = ImageContent(data="image data", mime_type="image/png")
    user_message = ChatMessageContent(
        role=AuthorRole.USER,
        items=[
            TextContent(text="Text content"),
            image_content,
        ],
    )
    formatted_user_message = format_user_message(user_message)

    assert len(formatted_user_message) == 2
    assert isinstance(formatted_user_message[0], Part)
    assert formatted_user_message[0].text == "Text content"
    assert isinstance(formatted_user_message[1], Part)
    assert formatted_user_message[1].inline_data.mime_type == "image/png"
    assert formatted_user_message[1].inline_data.data == image_content.data
