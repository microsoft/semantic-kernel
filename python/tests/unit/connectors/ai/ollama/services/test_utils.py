# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType

# The code under test
from semantic_kernel.connectors.ai.ollama.services.utils import (
    MESSAGE_CONVERTERS,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


@pytest.fixture
def mock_chat_message_content() -> ChatMessageContent:
    """Fixture to create a basic ChatMessageContent object with role=USER and simple text content."""
    return ChatMessageContent(
        role=AuthorRole.USER,
        content="Hello, I am a user message.",  # The text content
    )


@pytest.fixture
def mock_system_message_content() -> ChatMessageContent:
    """Fixture to create a ChatMessageContent object with role=SYSTEM."""
    return ChatMessageContent(role=AuthorRole.SYSTEM, content="This is a system message.")


@pytest.fixture
def mock_assistant_message_content() -> ChatMessageContent:
    """Fixture to create a ChatMessageContent object with role=ASSISTANT."""
    return ChatMessageContent(role=AuthorRole.ASSISTANT, content="This is an assistant message.")


@pytest.fixture
def mock_tool_message_content() -> ChatMessageContent:
    """Fixture to create a ChatMessageContent object with role=TOOL."""
    return ChatMessageContent(role=AuthorRole.TOOL, content="This is a tool message.")


def test_message_converters_system(mock_system_message_content: ChatMessageContent) -> None:
    """Test that passing a system message returns the correct dictionary structure for 'system' role."""
    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.SYSTEM]
    result = converter(mock_system_message_content)

    # Assert
    assert result["role"] == "system", "Expected role to be 'system' on the returned message."
    assert result["content"] == mock_system_message_content.content, (
        "Expected content to match the system message content."
    )


def test_message_converters_user_no_images(mock_chat_message_content: ChatMessageContent) -> None:
    """Test that passing a user message without images returns correct dictionary structure for 'user' role."""
    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.USER]
    result = converter(mock_chat_message_content)

    # Assert
    assert result["role"] == "user", "Expected role to be 'user' on the returned message."
    assert result["content"] == mock_chat_message_content.content, "Expected content to match the user message content."
    # Ensure that no 'images' field is added
    assert "images" not in result, "No images should be present if no ImageContent is added."


def test_message_converters_user_with_images() -> None:
    """Test user message with multiple images, verifying the 'images' field is populated."""
    # Arrange
    img1 = ImageContent(data="some_base64_data")
    img2 = ImageContent(data="other_base64_data")
    content = ChatMessageContent(role=AuthorRole.USER, items=[img1, img2], content="User with images")

    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.USER]
    result = converter(content)

    # Assert
    assert result["role"] == "user"
    assert result["content"] == content.content
    assert "images" in result, "Images field expected when ImageContent is present."
    assert len(result["images"]) == 2, "Two images should be in the 'images' field."
    assert result["images"] == [b"some_base64_data", b"other_base64_data"], (
        "Image data should match the content from ImageContent."
    )


def test_message_converters_user_with_image_missing_data() -> None:
    """Test user message with image content that has missing data, expecting ValueError."""
    # Arrange
    bad_image = ImageContent(data="")  # empty data for image
    content = ChatMessageContent(role=AuthorRole.USER, items=[bad_image])

    # Act & Assert
    converter = MESSAGE_CONVERTERS[AuthorRole.USER]
    with pytest.raises(ValueError) as exc_info:
        converter(content)

    assert "Image item must contain data encoded as base64." in str(exc_info.value), (
        "Should raise ValueError for missing base64 data in image."
    )


def test_message_converters_assistant_basic(mock_assistant_message_content: ChatMessageContent) -> None:
    """Test assistant message without images or tool calls."""
    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.ASSISTANT]
    result = converter(mock_assistant_message_content)

    # Assert
    assert result["role"] == "assistant", "Assistant role expected."
    assert result["content"] == mock_assistant_message_content.content
    assert "images" not in result, "No images included, so should not have an 'images' field."
    assert "tool_calls" not in result, "No FunctionCallContent, so 'tool_calls' field shouldn't be present."


def test_message_converters_assistant_with_image() -> None:
    """Test assistant message containing images. Verify 'images' field is added."""
    # Arrange
    img = ImageContent(data="assistant_base64_data")
    content = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[img], content="Assistant image message")

    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.ASSISTANT]
    result = converter(content)

    # Assert
    assert result["role"] == "assistant"
    assert result["content"] == content.content
    assert "images" in result, "Images should be included for assistant messages with ImageContent."
    assert result["images"] == [b"assistant_base64_data"], "Expected matching base64 data in images."


def test_message_converters_assistant_with_tool_calls() -> None:
    """Test assistant message with FunctionCallContent should populate 'tool_calls'."""
    # Arrange
    tool_call_1 = FunctionCallContent(function_name="foo", arguments='{"key": "value"}')
    tool_call_2 = FunctionCallContent(function_name="bar", arguments='{"another": "123"}')

    content = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[tool_call_1, tool_call_2], content="Assistant with tools"
    )

    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.ASSISTANT]
    result = converter(content)

    # Assert
    assert result["role"] == "assistant"
    assert result["content"] == content.content
    assert "tool_calls" in result, "tool_calls field should be present for assistant messages with FunctionCallContent."
    assert len(result["tool_calls"]) == 2, "Expected two tool calls in the result."
    assert result["tool_calls"][0]["function"]["name"] == "foo", "First tool call function name mismatched."
    assert result["tool_calls"][0]["function"]["arguments"] == {"key": "value"}, "Expected arguments to be JSON loaded."
    assert result["tool_calls"][1]["function"]["name"] == "bar", "Second tool call function name mismatched."
    assert result["tool_calls"][1]["function"]["arguments"] == {"another": "123"}, (
        "Expected arguments to be JSON loaded."
    )


def test_message_converters_tool_with_result() -> None:
    """Test tool message with a FunctionResultContent, verifying the message content is set."""
    # Arrange
    fr_content = FunctionResultContent(id="some_id", result="some result", function_name="test_func")
    tool_message = ChatMessageContent(role=AuthorRole.TOOL, items=[fr_content])

    # Act
    converter = MESSAGE_CONVERTERS[AuthorRole.TOOL]
    result = converter(tool_message)

    # Assert
    assert result["role"] == "tool", "Expected role to be 'tool' for a tool message."
    # The code takes the first FunctionResultContent's result as the content
    assert result["content"] == fr_content.result, "Expected content to match the function result."


def test_message_converters_tool_missing_function_result_content(mock_tool_message_content: ChatMessageContent) -> None:
    """Test that if no FunctionResultContent is present, ValueError is raised."""
    # Arrange
    mock_tool_message_content.items = []  # no FunctionResultContent in items
    converter = MESSAGE_CONVERTERS[AuthorRole.TOOL]

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        converter(mock_tool_message_content)
    assert "Tool message must have a function result content item." in str(exc_info.value)


@pytest.mark.parametrize("choice_type", [FunctionChoiceType.AUTO, FunctionChoiceType.NONE, FunctionChoiceType.REQUIRED])
def test_update_settings_from_function_choice_configuration(choice_type: FunctionChoiceType) -> None:
    """Test that update_settings_from_function_choice_configuration updates the settings with the correct tools."""
    # Arrange
    # We'll create a mock configuration with some available functions.
    mock_config = FunctionCallChoiceConfiguration()
    mock_config.available_functions = [MagicMock() for _ in range(2)]

    # We also patch the kernel_function_metadata_to_function_call_format function.
    # The function returns a dict object describing each function.
    mock_tool_description = {"type": "function", "function": {"name": "mocked_function"}}

    with patch(
        "semantic_kernel.connectors.ai.ollama.services.utils.kernel_function_metadata_to_function_call_format",
        return_value=mock_tool_description,
    ):
        settings = PromptExecutionSettings()

        # Act
        update_settings_from_function_choice_configuration(
            function_choice_configuration=mock_config,
            settings=settings,
            type=choice_type,
        )

    # Assert
    # After the call, either settings.tools or settings.extension_data["tools"] should be set.
    # The code tries settings.tools first and if it fails, it sets extension_data["tools"].
    # We'll check both possibilities.
    possible_tools = getattr(settings, "tools", None)

    if possible_tools is not None:
        # If settings.tools exists, ensure it got updated
        assert len(possible_tools) == 2, "Should have exactly two tools set in the settings.tools attribute."
        assert possible_tools[0]["function"]["name"] == "mocked_function", (
            "Expected mocked function name in settings.tools."
        )
    else:
        # Otherwise check for extension_data
        assert "tools" in settings.extension_data, "Expected 'tools' in extension_data if settings.tools not present."
        assert len(settings.extension_data["tools"]) == 2, "Should have exactly two tools in extension_data."
        assert settings.extension_data["tools"][0]["function"]["name"] == "mocked_function", (
            "Expected mocked function name in extension_data."
        )
