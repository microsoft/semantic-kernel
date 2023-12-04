# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.open_ai import (
    OpenAIRequestSettings,
)


def test_default_complete_request_settings():
    settings = OpenAIRequestSettings()
    assert settings.temperature == 0.0
    assert settings.top_p == 1.0
    assert settings.presence_penalty == 0.0
    assert settings.frequency_penalty == 0.0
    assert settings.max_tokens == 256
    assert settings.stop is None
    assert settings.number_of_responses == 1
    assert settings.logprobs is None
    assert settings.logit_bias == {}
    assert settings.messages[0]["content"] == "Assistant is a large language model."


def test_custom_complete_request_settings():
    settings = OpenAIRequestSettings(
        temperature=0.5,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=128,
        stop_sequences=["\n"],
        number_of_responses=2,
        logprobs=1,
        token_selection_biases={1: 1},
        messages=[{"role": "system", "content": "Hello"}],
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.presence_penalty == 0.5
    assert settings.frequency_penalty == 0.5
    assert settings.max_tokens == 128
    assert settings.stop_sequences == ["\n"]
    assert settings.number_of_responses == 2
    assert settings.logprobs == 1
    assert settings.token_selection_biases == {1: 1}
    assert settings.chat_system_prompt == [{"role": "system", "content": "Hello"}]


def test_complete_request_settings_from_default_completion_config():
    settings = OpenAIRequestSettings()
    chat_settings = OpenAIRequestSettings.from_ai_request(settings)
    chat_settings = OpenAIRequestSettings()
    assert chat_settings.temperature == 0.0
    assert chat_settings.top_p == 1.0
    assert chat_settings.presence_penalty == 0.0
    assert chat_settings.frequency_penalty == 0.0
    assert chat_settings.max_tokens == 256
    assert chat_settings.stop_sequences == []
    assert chat_settings.number_of_responses == 1
    assert chat_settings.token_selection_biases == {}


def test_chat_request_settings_from_custom_completion_config():
    settings = OpenAIRequestSettings(
        temperature=0.5,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=128,
        stop_sequences=["\n"],
        number_of_responses=2,
        logprobs=1,
        token_selection_biases={1: 1},
        chat_system_prompt="Hello",
    )
    chat_settings = OpenAIRequestSettings.from_ai_request(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop_sequences == ["\n"]
    assert chat_settings.number_of_responses == 2
    assert chat_settings.token_selection_biases == {1: 1}
