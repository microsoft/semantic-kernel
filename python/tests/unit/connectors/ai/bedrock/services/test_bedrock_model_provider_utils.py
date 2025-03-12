# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import (
    BedrockModelProvider,
)
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import (
    MESSAGE_CONVERTERS,
    finish_reason_from_bedrock_to_semantic_kernel,
    remove_none_recursively,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError
from semantic_kernel.kernel import Kernel


def test_remove_none_recursively():
    data = {
        "a": 1,
        "b": None,
        "c": {
            "d": 2,
            "e": None,
            "f": {
                "g": 3,
                "h": None,
            },
        },
    }
    expected = {
        "a": 1,
        "c": {
            "d": 2,
            "f": {
                "g": 3,
            },
        },
    }
    assert remove_none_recursively(data) == expected


def test_remove_recursively_max_depth():
    data = {
        "a": {"b": None},
    }

    assert remove_none_recursively(data, max_depth=1) == data


def test_update_settings_from_function_choice_configuration_auto(kernel: Kernel, custom_plugin_class) -> None:
    kernel.add_plugin(plugin=custom_plugin_class(), plugin_name="custom_plugin")

    settings = BedrockChatPromptExecutionSettings()

    auto_function_choice_behavior = FunctionChoiceBehavior.Auto()
    auto_function_choice_behavior.configure(
        kernel,
        update_settings_from_function_choice_configuration,
        settings,
    )

    assert "auto" in settings.tool_choice
    assert len(settings.tools) == 1


def test_update_settings_from_function_choice_configuration_auto_without_plugin(kernel: Kernel) -> None:
    settings = BedrockChatPromptExecutionSettings()

    auto_function_choice_behavior = FunctionChoiceBehavior.Auto()
    auto_function_choice_behavior.configure(
        kernel,
        update_settings_from_function_choice_configuration,
        settings,
    )

    assert settings.tool_choice is None
    assert settings.tools is None


def test_update_settings_from_function_choice_configuration_none(kernel: Kernel) -> None:
    settings = BedrockChatPromptExecutionSettings()

    auto_function_choice_behavior = FunctionChoiceBehavior.NoneInvoke()
    auto_function_choice_behavior.configure(
        kernel,
        update_settings_from_function_choice_configuration,
        settings,
    )

    assert settings.tool_choice is None
    assert settings.tools is None


def test_update_settings_from_function_choice_configuration_required_with_one_function(
    kernel: Kernel,
    custom_plugin_class,
) -> None:
    kernel.add_plugin(plugin=custom_plugin_class(), plugin_name="custom_plugin")

    settings = BedrockChatPromptExecutionSettings()

    auto_function_choice_behavior = FunctionChoiceBehavior.Required()
    auto_function_choice_behavior.configure(
        kernel,
        update_settings_from_function_choice_configuration,
        settings,
    )

    assert "tool" in settings.tool_choice
    assert len(settings.tools) == 1


def test_update_settings_from_function_choice_configuration_required_with_more_than_one_functions(
    kernel: Kernel,
    custom_plugin_class,
    experimental_plugin_class,
) -> None:
    kernel.add_plugin(plugin=custom_plugin_class(), plugin_name="custom_plugin")
    kernel.add_plugin(plugin=experimental_plugin_class(), plugin_name="experimental_plugin")

    settings = BedrockChatPromptExecutionSettings()

    auto_function_choice_behavior = FunctionChoiceBehavior.Required()
    auto_function_choice_behavior.configure(
        kernel,
        update_settings_from_function_choice_configuration,
        settings,
    )

    assert "any" in settings.tool_choice
    assert len(settings.tools) == 2


def test_inference_profile_with_bedrock_model() -> None:
    """Test the BedrockModelProvider class returns the correct model for a given inference profile."""

    us_amazon_inference_profile = "us.amazon.nova-lite-v1:0"
    assert BedrockModelProvider.to_model_provider(us_amazon_inference_profile) == BedrockModelProvider.AMAZON

    us_anthropic_inference_profile = "us.anthropic.claude-3-sonnet-20240229-v1:0"
    assert BedrockModelProvider.to_model_provider(us_anthropic_inference_profile) == BedrockModelProvider.ANTHROPIC

    eu_meta_inference_profile = "eu.meta.llama3-2-3b-instruct-v1:0"
    assert BedrockModelProvider.to_model_provider(eu_meta_inference_profile) == BedrockModelProvider.META

    unknown_inference_profile = "unknown"
    with pytest.raises(ValueError, match="Model ID unknown does not contain a valid model provider name."):
        BedrockModelProvider.to_model_provider(unknown_inference_profile)


def test_remove_none_recursively_empty_dict() -> None:
    """Test that an empty dict returns an empty dict."""
    assert remove_none_recursively({}) == {}


def test_remove_none_recursively_no_none() -> None:
    """Test that a dict with no None values remains the same."""
    original = {"a": 1, "b": 2}
    result = remove_none_recursively(original)
    assert result == {"a": 1, "b": 2}


def test_remove_none_recursively_with_none() -> None:
    """Test that dict values of None are removed."""
    original = {"a": 1, "b": None, "c": {"d": None, "e": 3}}
    result = remove_none_recursively(original)
    # 'b' should be removed and 'd' inside nested dict should be removed
    assert result == {"a": 1, "c": {"e": 3}}


def test_remove_none_recursively_max_depth() -> None:
    """Test that the function respects max_depth."""
    original = {"a": {"b": {"c": None}}}
    # If max_depth=1, it won't go deep enough to remove 'c'.
    result = remove_none_recursively(original, max_depth=1)
    assert result == {"a": {"b": {"c": None}}}

    # If max_depth=3, it should remove 'c'.
    result = remove_none_recursively(original, max_depth=3)
    assert result == {"a": {"b": {}}}


def test_format_system_message() -> None:
    """Test that system message is formatted correctly."""
    content = ChatMessageContent(role=AuthorRole.SYSTEM, content="System message")
    formatted = MESSAGE_CONVERTERS[AuthorRole.SYSTEM](content)
    assert formatted == {"text": "System message"}


def test_format_user_message_text_only() -> None:
    """Test user message with only text content."""
    text_item = TextContent(text="Hello!")
    user_message = ChatMessageContent(role=AuthorRole.USER, items=[text_item])

    formatted = MESSAGE_CONVERTERS[AuthorRole.USER](user_message)
    assert formatted["role"] == "user"
    assert len(formatted["content"]) == 1
    assert formatted["content"][0] == {"text": "Hello!"}


def test_format_user_message_image_only() -> None:
    """Test user message with only image content."""
    img_item = ImageContent(data=b"abc", mime_type="image/png")
    user_message = ChatMessageContent(role=AuthorRole.USER, items=[img_item])

    formatted = MESSAGE_CONVERTERS[AuthorRole.USER](user_message)
    assert formatted["role"] == "user"
    assert len(formatted["content"]) == 1
    image_section = formatted["content"][0].get("image")
    assert image_section["format"] == "png"
    assert image_section["source"]["bytes"] == b"abc"


def test_format_user_message_unsupported_content() -> None:
    """Test user message raises error with unsupported content type."""
    # We can simulate an unsupported content type by using FunctionCallContent.
    func_call_item = FunctionCallContent(id="123", function_name="test_function", arguments="{}")
    user_message = ChatMessageContent(role=AuthorRole.USER, items=[func_call_item])

    with pytest.raises(ServiceInvalidRequestError) as exc:
        MESSAGE_CONVERTERS[AuthorRole.USER](user_message)

    assert "Only text and image content are supported in a user message." in str(exc.value)


def test_format_assistant_message_text_content() -> None:
    """Test assistant message with text content."""
    text_item = TextContent(text="Assistant response")
    assistant_message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[text_item])

    formatted = MESSAGE_CONVERTERS[AuthorRole.ASSISTANT](assistant_message)
    assert formatted["role"] == "assistant"
    assert formatted["content"] == [{"text": "Assistant response"}]


def test_format_assistant_message_function_call_content() -> None:
    """Test assistant message with function call content."""
    func_item = FunctionCallContent(
        id="fc1", plugin_name="plugin", function_name="function", arguments='{"param": "value"}'
    )
    assistant_message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[func_item])

    formatted = MESSAGE_CONVERTERS[AuthorRole.ASSISTANT](assistant_message)
    assert len(formatted["content"]) == 1
    tool_use = formatted["content"][0].get("toolUse")
    assert tool_use
    assert tool_use["toolUseId"] == "fc1"
    assert tool_use["name"] == "plugin-function"
    assert tool_use["input"] == {"param": "value"}


def test_format_assistant_message_image_content_raises() -> None:
    """Test assistant message with image raises error."""
    img_item = ImageContent(data=b"abc", mime_type="image/jpeg")
    assistant_message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[img_item])

    with pytest.raises(ServiceInvalidRequestError) as exc:
        MESSAGE_CONVERTERS[AuthorRole.ASSISTANT](assistant_message)

    assert "Image content is not supported in an assistant message." in str(exc.value)


def test_format_assistant_message_unsupported_type() -> None:
    """Test assistant message with unsupported item content type."""
    func_res_item = FunctionResultContent(id="res1", function_name="some_function", result="some_result")
    assistant_message = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[func_res_item])

    with pytest.raises(ServiceInvalidRequestError) as exc:
        MESSAGE_CONVERTERS[AuthorRole.ASSISTANT](assistant_message)
    assert "Unsupported content type in an assistant message:" in str(exc.value)


def test_format_tool_message_text() -> None:
    """Test tool message with text content."""
    text_item = TextContent(text="Some text")
    tool_message = ChatMessageContent(role=AuthorRole.TOOL, items=[text_item])

    formatted = MESSAGE_CONVERTERS[AuthorRole.TOOL](tool_message)
    assert formatted["role"] == "user"  # note that for a tool message, role set to 'user'
    assert formatted["content"] == [{"text": "Some text"}]


def test_format_tool_message_function_result() -> None:
    """Test tool message with function result content."""
    func_result_item = FunctionResultContent(id="res_id", function_name="test_function", result="some result")
    tool_message = ChatMessageContent(role=AuthorRole.TOOL, items=[func_result_item])

    formatted = MESSAGE_CONVERTERS[AuthorRole.TOOL](tool_message)
    assert formatted["role"] == "user"
    content = formatted["content"][0]
    assert content.get("toolResult")
    assert content["toolResult"]["toolUseId"] == "res_id"
    assert content["toolResult"]["content"] == [{"text": "some result"}]


def test_format_tool_message_image_raises() -> None:
    """Test tool message with image content raises an error."""
    img_item = ImageContent(data=b"xyz", mime_type="image/jpeg")
    tool_message = ChatMessageContent(role=AuthorRole.TOOL, items=[img_item])

    with pytest.raises(ServiceInvalidRequestError) as exc:
        MESSAGE_CONVERTERS[AuthorRole.TOOL](tool_message)
    assert "Image content is not supported in a tool message." in str(exc.value)


def test_finish_reason_from_bedrock_to_semantic_kernel_stop() -> None:
    """Test that 'stop_sequence' maps to FinishReason.STOP"""
    reason = finish_reason_from_bedrock_to_semantic_kernel("stop_sequence")
    assert reason == FinishReason.STOP

    reason = finish_reason_from_bedrock_to_semantic_kernel("end_turn")
    assert reason == FinishReason.STOP


def test_finish_reason_from_bedrock_to_semantic_kernel_length() -> None:
    """Test that 'max_tokens' maps to FinishReason.LENGTH"""
    reason = finish_reason_from_bedrock_to_semantic_kernel("max_tokens")
    assert reason == FinishReason.LENGTH


def test_finish_reason_from_bedrock_to_semantic_kernel_content_filtered() -> None:
    """Test that 'content_filtered' maps to FinishReason.CONTENT_FILTER"""
    reason = finish_reason_from_bedrock_to_semantic_kernel("content_filtered")
    assert reason == FinishReason.CONTENT_FILTER


def test_finish_reason_from_bedrock_to_semantic_kernel_tool_use() -> None:
    """Test that 'tool_use' maps to FinishReason.TOOL_CALLS"""
    reason = finish_reason_from_bedrock_to_semantic_kernel("tool_use")
    assert reason == FinishReason.TOOL_CALLS


def test_finish_reason_from_bedrock_to_semantic_kernel_unknown() -> None:
    """Test that unknown finish reason returns None"""
    reason = finish_reason_from_bedrock_to_semantic_kernel("something_unknown")
    assert reason is None


@pytest.fixture
def mock_bedrock_settings() -> BedrockChatPromptExecutionSettings:
    """Helper fixture for BedrockChatPromptExecutionSettings."""
    return BedrockChatPromptExecutionSettings()


@pytest.fixture
def mock_function_choice_config() -> FunctionCallChoiceConfiguration:
    """Helper fixture for a sample FunctionCallChoiceConfiguration."""

    # We'll create mock kernel functions with metadata
    mock_func_1 = MagicMock()
    mock_func_1.fully_qualified_name = "plugin-function1"
    mock_func_1.description = "Function 1 description"

    param1 = MagicMock()
    param1.name = "param1"
    param1.schema_data = {"type": "string"}
    param1.is_required = True

    param2 = MagicMock()
    param2.name = "param2"
    param2.schema_data = {"type": "integer"}
    param2.is_required = False

    mock_func_1.parameters = [
        param1,
        param2,
    ]
    mock_func_2 = MagicMock()
    mock_func_2.fully_qualified_name = "plugin-function2"
    mock_func_2.description = "Function 2 description"
    mock_func_2.parameters = []

    config = FunctionCallChoiceConfiguration()
    config.available_functions = [mock_func_1, mock_func_2]

    return config


def test_update_settings_from_function_choice_configuration_none_type(
    mock_function_choice_config, mock_bedrock_settings
) -> None:
    """Test that if the FunctionChoiceType is NONE it doesn't modify settings."""
    update_settings_from_function_choice_configuration(
        mock_function_choice_config, mock_bedrock_settings, FunctionChoiceType.NONE
    )
    assert mock_bedrock_settings.tool_choice is None
    assert mock_bedrock_settings.tools is None


def test_update_settings_from_function_choice_configuration_auto_two_tools(
    mock_function_choice_config, mock_bedrock_settings
) -> None:
    """Test that AUTO sets tool_choice to {"auto": {}} and sets tools list"""
    update_settings_from_function_choice_configuration(
        mock_function_choice_config, mock_bedrock_settings, FunctionChoiceType.AUTO
    )
    assert mock_bedrock_settings.tool_choice == {"auto": {}}
    assert len(mock_bedrock_settings.tools) == 2
    # Validate structure of first tool
    tool_spec_1 = mock_bedrock_settings.tools[0].get("toolSpec")
    assert tool_spec_1["name"] == "plugin-function1"
    assert tool_spec_1["description"] == "Function 1 description"


def test_update_settings_from_function_choice_configuration_required_many(
    mock_function_choice_config, mock_bedrock_settings
) -> None:
    """Test that REQUIRED with more than one function sets tool_choice to {"any": {}}."""
    update_settings_from_function_choice_configuration(
        mock_function_choice_config, mock_bedrock_settings, FunctionChoiceType.REQUIRED
    )
    assert mock_bedrock_settings.tool_choice == {"any": {}}
    assert len(mock_bedrock_settings.tools) == 2


def test_update_settings_from_function_choice_configuration_required_one(mock_bedrock_settings) -> None:
    """Test that REQUIRED with a single function picks "tool" with that function name."""
    single_func = MagicMock()
    single_func.fully_qualified_name = "plugin-function"
    single_func.description = "Only function"
    single_func.parameters = []

    config = FunctionCallChoiceConfiguration()
    config.available_functions = [single_func]

    update_settings_from_function_choice_configuration(config, mock_bedrock_settings, FunctionChoiceType.REQUIRED)
    assert mock_bedrock_settings.tool_choice == {"tool": {"name": "plugin-function"}}
    assert len(mock_bedrock_settings.tools) == 1
    assert mock_bedrock_settings.tools[0]["toolSpec"]["name"] == "plugin-function"
