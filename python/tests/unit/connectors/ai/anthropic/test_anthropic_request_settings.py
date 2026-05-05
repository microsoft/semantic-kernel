# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicCacheSettings,
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError


def test_default_anthropic_chat_prompt_execution_settings():
    settings = AnthropicChatPromptExecutionSettings()
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.max_tokens == 1024
    assert settings.messages is None


def test_custom_anthropic_chat_prompt_execution_settings():
    settings = AnthropicChatPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        max_tokens=128,
        messages=[{"role": "system", "content": "Hello"}],
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.max_tokens == 128
    assert settings.messages == [{"role": "system", "content": "Hello"}]


def test_anthropic_chat_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.max_tokens == 1024


def test_anthropic_chat_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = AnthropicChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = AnthropicChatPromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)
    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_anthropic_chat_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_openai_chat_prompt_execution_settings_from_custom_completion_config_with_none():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_openai_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "tools": [{}],
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_create_options():
    settings = AnthropicChatPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "tools": [{}],
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    options = settings.prepare_settings_dict()
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["max_tokens"] == 128


def test_tool_choice_none():
    with pytest.raises(ServiceInvalidExecutionSettingsError, match="Tool choice 'none' is not supported by Anthropic."):
        AnthropicChatPromptExecutionSettings(
            service_id="test_service",
            extension_data={
                "temperature": 0.5,
                "top_p": 0.5,
                "max_tokens": 128,
                "tool_choice": {"type": "none"},
                "messages": [{"role": "system", "content": "Hello"}],
            },
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke(),
        )


# region AnthropicCacheSettings


def test_cache_settings_default_is_off():
    settings = AnthropicCacheSettings()
    assert settings.enabled is False
    assert settings.cache_system is False
    assert settings.cache_tools is False
    assert settings.ttl == "5m"


def test_cache_settings_on():
    settings = AnthropicCacheSettings.on()
    assert settings.enabled is True
    assert settings.cache_system is True
    assert settings.cache_tools is True
    assert settings.ttl == "5m"


def test_cache_settings_on_with_1h_ttl():
    settings = AnthropicCacheSettings.on(ttl="1h")
    assert settings.enabled is True
    assert settings.ttl == "1h"


def test_cache_settings_off():
    settings = AnthropicCacheSettings.off()
    assert settings.enabled is False


def test_cache_settings_system_only():
    settings = AnthropicCacheSettings.system()
    assert settings.enabled is True
    assert settings.cache_system is True
    assert settings.cache_tools is False


def test_cache_settings_tools_only():
    settings = AnthropicCacheSettings.tools()
    assert settings.enabled is True
    assert settings.cache_system is False
    assert settings.cache_tools is True


def test_cache_control_5m():
    ctrl = AnthropicCacheSettings.on(ttl="5m")._cache_control()
    assert ctrl == {"type": "ephemeral"}


def test_cache_control_1h():
    ctrl = AnthropicCacheSettings.on(ttl="1h")._cache_control()
    assert ctrl == {"type": "ephemeral", "ttl": "1h"}


def test_cache_settings_short():
    settings = AnthropicCacheSettings.short()
    assert settings.enabled is True
    assert settings.cache_system is True
    assert settings.cache_tools is True
    assert settings.ttl == "5m"


def test_cache_settings_long():
    settings = AnthropicCacheSettings.long()
    assert settings.enabled is True
    assert settings.cache_system is True
    assert settings.cache_tools is True
    assert settings.ttl == "1h"


# endregion

# region prepare_settings_dict with caching


def test_prepare_settings_dict_cache_off_no_injection():
    settings = AnthropicChatPromptExecutionSettings(
        system="You are a helpful assistant.",
        tools=[{"name": "search", "description": "Search the web"}],
        cache=AnthropicCacheSettings.off(),
    )
    data = settings.prepare_settings_dict()
    assert data["system"] == "You are a helpful assistant."
    assert "cache_control" not in data["tools"][-1]


def test_prepare_settings_dict_cache_system_only():
    settings = AnthropicChatPromptExecutionSettings(
        system="You are a helpful assistant.",
        cache=AnthropicCacheSettings.system(),
    )
    data = settings.prepare_settings_dict()
    assert isinstance(data["system"], list)
    assert data["system"] == [
        {"type": "text", "text": "You are a helpful assistant.", "cache_control": {"type": "ephemeral"}}
    ]


def test_prepare_settings_dict_cache_tools_only():
    tools = [
        {"name": "tool_a", "description": "Tool A"},
        {"name": "tool_b", "description": "Tool B"},
    ]
    settings = AnthropicChatPromptExecutionSettings(
        tools=tools,
        cache=AnthropicCacheSettings.tools(),
    )
    data = settings.prepare_settings_dict()
    assert "cache_control" not in data["tools"][0]
    assert data["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    # original tools list must not be mutated
    assert "cache_control" not in tools[-1]


def test_prepare_settings_dict_cache_on_system_and_tools():
    tools = [{"name": "search", "description": "Search the web"}]
    settings = AnthropicChatPromptExecutionSettings(
        system="You are a helpful assistant.",
        tools=tools,
        cache=AnthropicCacheSettings.on(),
    )
    data = settings.prepare_settings_dict()
    assert isinstance(data["system"], list)
    assert data["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert data["tools"][-1]["cache_control"] == {"type": "ephemeral"}


def test_prepare_settings_dict_cache_on_1h_ttl():
    tools = [{"name": "search", "description": "Search the web"}]
    settings = AnthropicChatPromptExecutionSettings(
        system="You are a helpful assistant.",
        tools=tools,
        cache=AnthropicCacheSettings.on(ttl="1h"),
    )
    data = settings.prepare_settings_dict()
    assert data["system"][0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert data["tools"][-1]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


def test_prepare_settings_dict_cache_system_already_list():
    """When system is pre-structured as list[dict], cache_control is injected on the last block."""
    system_blocks = [
        {"type": "text", "text": "First block."},
        {"type": "text", "text": "Second block."},
    ]
    settings = AnthropicChatPromptExecutionSettings(
        system=system_blocks,
        cache=AnthropicCacheSettings.system(),
    )
    data = settings.prepare_settings_dict()
    assert isinstance(data["system"], list)
    assert "cache_control" not in data["system"][0]
    assert data["system"][-1]["cache_control"] == {"type": "ephemeral"}
    # original list must not be mutated
    assert "cache_control" not in system_blocks[-1]


def test_prepare_settings_dict_cache_system_empty_string_no_injection():
    """Empty system string should not be wrapped in a cache block."""
    settings = AnthropicChatPromptExecutionSettings(
        system="",
        cache=AnthropicCacheSettings.system(),
    )
    data = settings.prepare_settings_dict()
    # empty string — no injection expected
    assert not isinstance(data.get("system"), list)


def test_prepare_settings_dict_cache_tools_empty_no_injection():
    """No tools present — cache_tools flag should be a no-op."""
    settings = AnthropicChatPromptExecutionSettings(
        cache=AnthropicCacheSettings.tools(),
    )
    data = settings.prepare_settings_dict()
    assert data.get("tools") is None


def test_prepare_settings_dict_cache_excluded_from_serialization():
    """The cache field must not appear in the serialized API payload."""
    settings = AnthropicChatPromptExecutionSettings(cache=AnthropicCacheSettings.on())
    data = settings.prepare_settings_dict()
    assert "cache" not in data


# endregion
