# Copyright (c) Microsoft. All rights reserved.

import pytest
from google.cloud.aiplatform_v1beta1.types.content import Candidate
from vertexai.generative_models import Part

from semantic_kernel.connectors.ai.google.vertex_ai.services.utils import (
    finish_reason_from_vertex_ai_to_semantic_kernel,
    format_assistant_message,
    format_user_message,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError


def test_finish_reason_from_vertex_ai_to_semantic_kernel():
    """Test finish_reason_from_vertex_ai_to_semantic_kernel."""
    assert finish_reason_from_vertex_ai_to_semantic_kernel(Candidate.FinishReason.STOP) == FinishReason.STOP
    assert finish_reason_from_vertex_ai_to_semantic_kernel(Candidate.FinishReason.MAX_TOKENS) == FinishReason.LENGTH
    assert finish_reason_from_vertex_ai_to_semantic_kernel(Candidate.FinishReason.SAFETY) == FinishReason.CONTENT_FILTER
    assert finish_reason_from_vertex_ai_to_semantic_kernel(Candidate.FinishReason.OTHER) is None


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


def test_format_user_message_throws_with_unsupported_items() -> None:
    """Test format_user_message with unsupported items."""
    # Test with unsupported items, any item other than TextContent and ImageContent should raise an error
    user_message = ChatMessageContent(
        role=AuthorRole.USER,
        items=[
            FunctionCallContent(),
        ],
    )
    with pytest.raises(ServiceInvalidRequestError):
        format_user_message(user_message)

    # Test with an ImageContent that has no data_uri
    user_message = ChatMessageContent(
        role=AuthorRole.USER,
        items=[
            ImageContent(data_uri=""),
        ],
    )
    with pytest.raises(ServiceInvalidRequestError):
        format_user_message(user_message)


def test_format_assistant_message() -> None:
    assistant_message = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=[
            TextContent(text="test"),
            FunctionCallContent(name="test_function", arguments={}),
            ImageContent(data="image data", mime_type="image/png"),
        ],
    )

    formatted_assistant_message = format_assistant_message(assistant_message)
    assert isinstance(formatted_assistant_message, list)
    assert len(formatted_assistant_message) == 3
    assert isinstance(formatted_assistant_message[0], Part)
    assert formatted_assistant_message[0].text == "test"
    assert isinstance(formatted_assistant_message[1], Part)
    assert formatted_assistant_message[1].function_call.name == "test_function"
    assert formatted_assistant_message[1].function_call.args == {}
    assert isinstance(formatted_assistant_message[2], Part)
    assert formatted_assistant_message[2].inline_data


def test_format_assistant_message_with_unsupported_items() -> None:
    assistant_message = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=[
            FunctionResultContent(id="test_id", function_name="test_function"),
        ],
    )

    with pytest.raises(ServiceInvalidRequestError):
        format_assistant_message(assistant_message)


def test_format_assistant_message_with_thought_signature() -> None:
    """Test that thought_signature is preserved in function call parts for Vertex AI."""
    import base64

    thought_sig = base64.b64encode(b"test_thought_signature_data").decode("utf-8")
    assistant_message = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=[
            FunctionCallContent(
                name="test_function",
                arguments={"arg1": "value1"},
                metadata={"thought_signature": thought_sig},
            ),
        ],
    )

    formatted = format_assistant_message(assistant_message)
    assert len(formatted) == 1
    assert isinstance(formatted[0], Part)
    assert formatted[0].function_call.name == "test_function"
    assert formatted[0].function_call.args == {"arg1": "value1"}
    part_dict = formatted[0].to_dict()
    assert "thought_signature" in part_dict
    assert part_dict["thought_signature"] == thought_sig


def test_format_assistant_message_without_thought_signature() -> None:
    """Test that function calls without thought_signature still work for Vertex AI."""
    assistant_message = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=[
            FunctionCallContent(
                name="test_function",
                arguments={"arg1": "value1"},
            ),
        ],
    )

    formatted = format_assistant_message(assistant_message)
    assert len(formatted) == 1
    assert isinstance(formatted[0], Part)
    assert formatted[0].function_call.name == "test_function"
    assert formatted[0].function_call.args == {"arg1": "value1"}
    part_dict = formatted[0].to_dict()
    assert "thought_signature" not in part_dict
