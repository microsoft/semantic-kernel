# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)


def test_default_complete_request_settings():
    settings = CompleteRequestSettings()
    assert settings.temperature == 0.0
    assert settings.top_p == 1.0
    assert settings.presence_penalty == 0.0
    assert settings.frequency_penalty == 0.0
    assert settings.max_tokens == 256
    assert settings.stop_sequences == []
    assert settings.number_of_responses == 1
    assert settings.logprobs == 0
    assert settings.token_selection_biases == {}
    assert settings.chat_system_prompt == "Assistant is a large language model."


def test_custom_complete_request_settings():
    settings = CompleteRequestSettings(
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
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.presence_penalty == 0.5
    assert settings.frequency_penalty == 0.5
    assert settings.max_tokens == 128
    assert settings.stop_sequences == ["\n"]
    assert settings.number_of_responses == 2
    assert settings.logprobs == 1
    assert settings.token_selection_biases == {1: 1}
    assert settings.chat_system_prompt == "Hello"


def test_default_chat_request_settings():
    settings = ChatRequestSettings()
    assert settings.temperature == 0.0
    assert settings.top_p == 1.0
    assert settings.presence_penalty == 0.0
    assert settings.frequency_penalty == 0.0
    assert settings.max_tokens == 256
    assert settings.stop_sequences == []
    assert settings.number_of_responses == 1
    assert settings.token_selection_biases == {}


def test_complete_request_settings_from_default_completion_config():
    settings = CompleteRequestSettings()
    chat_settings = ChatRequestSettings.from_completion_config(settings)
    chat_settings = ChatRequestSettings()
    assert chat_settings.temperature == 0.0
    assert chat_settings.top_p == 1.0
    assert chat_settings.presence_penalty == 0.0
    assert chat_settings.frequency_penalty == 0.0
    assert chat_settings.max_tokens == 256
    assert chat_settings.stop_sequences == []
    assert chat_settings.number_of_responses == 1
    assert chat_settings.token_selection_biases == {}


def test_chat_request_settings_from_custom_completion_config():
    settings = CompleteRequestSettings(
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
    chat_settings = ChatRequestSettings.from_completion_config(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop_sequences == ["\n"]
    assert chat_settings.number_of_responses == 2
    assert chat_settings.token_selection_biases == {1: 1}
