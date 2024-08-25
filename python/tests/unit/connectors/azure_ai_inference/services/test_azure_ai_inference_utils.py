# Copyright (c) Microsoft. All rights reserved.


import pytest
from azure.ai.inference.models import (
    AssistantMessage,
    ImageContentItem,
    SystemMessage,
    TextContentItem,
    ToolMessage,
    UserMessage,
)

from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import (
    MESSAGE_CONVERTERS,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole


def test_message_convertors_contain_all_author_roles() -> None:
    """Test that all AuthorRoles are present in the MESSAGE_CONVERTERS dict."""
    for role in AuthorRole:
        assert role in MESSAGE_CONVERTERS


def test_format_system_message() -> None:
    """Test that a system message is formatted correctly."""
    message = ChatMessageContent(role=AuthorRole.SYSTEM, content="test content")
    system_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(system_message, SystemMessage)
    assert system_message.content == message.content


def test_format_user_message_with_no_image() -> None:
    """Test that a user message with no image items is formatted correctly."""
    message = ChatMessageContent(role=AuthorRole.USER, content="test content")
    user_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(user_message, UserMessage)
    assert user_message.content == message.content


def test_format_user_message_with_image() -> None:
    """Test that a user message with image items is formatted correctly"""
    message = ChatMessageContent(
        role=AuthorRole.USER,
        items=[
            TextContent(text="test text"),
            ImageContent(uri="https://test.com/image.jpg"),
        ],
    )
    user_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(user_message, UserMessage)
    assert len(user_message.content) == 2
    assert isinstance(user_message.content[0], TextContentItem)
    assert isinstance(user_message.content[1], ImageContentItem)


def test_format_user_message_with_unsupported_items() -> None:
    """Test that a user message with unsupported items is formatted correctly"""
    message = ChatMessageContent(
        role=AuthorRole.USER,
        items=[
            TextContent(text="test text"),
            ImageContent(),  # ImageContent without uri or data_uri is unsupported
            FunctionCallContent(id="test function"),  # FunctionCallContent unsupported
        ],
    )
    user_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(user_message, UserMessage)
    assert len(user_message.content) == 1
    assert isinstance(user_message.content[0], TextContentItem)


def test_format_assistant_message() -> None:
    """Test that an assistant message is formatted correctly."""
    message = ChatMessageContent(role=AuthorRole.ASSISTANT, content="test content")
    assistant_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(assistant_message, AssistantMessage)
    assert assistant_message.content == message.content


def test_format_assistant_message_with_tool_call() -> None:
    """Test that an assistant message with a tool call is formatted correctly."""
    function_call_content = FunctionCallContent(id="test function")

    message = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=[function_call_content],
    )
    assistant_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(assistant_message, AssistantMessage)
    assert assistant_message.content == message.content
    assert len(assistant_message.tool_calls) == 1
    assert assistant_message.tool_calls[0].id == function_call_content.id


def test_format_assistant_message_with_unsupported_items() -> None:
    """Test that an assistant message with unsupported items is formatted correctly."""
    text_content = TextContent(text="test text")

    message = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        items=[
            text_content,
            ImageContent(),  # ImageContent is unsupported
        ],
    )
    assistant_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(assistant_message, AssistantMessage)
    assert assistant_message.content == message.content


def test_format_tool_message() -> None:
    """Test that a tool message is formatted correctly."""
    function_result_content = FunctionResultContent(
        id="test function", result="test result"
    )

    message = ChatMessageContent(
        role=AuthorRole.TOOL,
        items=[function_result_content],
    )
    tool_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == function_result_content.result
    assert tool_message.tool_call_id == function_result_content.id


def test_format_tool_message_item_not_found_as_the_first_item() -> None:
    """Test that formatting a tool message where the function result item is not the first item."""
    function_result_content = FunctionResultContent(
        id="test function", result="test result"
    )

    message = ChatMessageContent(
        role=AuthorRole.TOOL,
        items=[
            TextContent(text="test text"),
            function_result_content,
        ],
    )

    with pytest.raises(ValueError):
        MESSAGE_CONVERTERS[message.role](message)


def test_format_tool_message_with_more_than_one_items() -> None:
    """Test that a tool message with more than one item is formatted correctly."""
    function_result_content = FunctionResultContent(
        id="test function", result="test result"
    )

    message = ChatMessageContent(
        role=AuthorRole.TOOL,
        items=[
            function_result_content,
            TextContent(text="test text"),
        ],
    )
    tool_message = MESSAGE_CONVERTERS[message.role](message)

    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == function_result_content.result
    assert tool_message.tool_call_id == function_result_content.id
