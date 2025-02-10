# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import (
    BedrockModelProvider,
)
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import (
    remove_none_recursively,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
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
