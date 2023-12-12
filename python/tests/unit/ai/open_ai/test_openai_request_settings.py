# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
)


def test_default_openai_chat_request_settings():
    settings = OpenAIChatRequestSettings()
    assert settings.temperature == 0.0
    assert settings.top_p == 1.0
    assert settings.presence_penalty == 0.0
    assert settings.frequency_penalty == 0.0
    assert settings.max_tokens == 256
    assert settings.stop is None
    assert settings.number_of_responses == 1
    assert settings.logit_bias == {}
    assert settings.messages[0]["content"] == "Assistant is a large language model."
    assert settings.response_format == "text"


def test_custom_openai_chat_request_settings():
    settings = OpenAIChatRequestSettings(
        temperature=0.5,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=128,
        stop="\n",
        number_of_responses=2,
        logit_bias={"1": 1},
        messages=[{"role": "system", "content": "Hello"}],
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.presence_penalty == 0.5
    assert settings.frequency_penalty == 0.5
    assert settings.max_tokens == 128
    assert settings.stop == "\n"
    assert settings.number_of_responses == 2
    assert settings.logit_bias == {"1": 1}
    assert settings.messages == [{"role": "system", "content": "Hello"}]


def test_openai_chat_request_settings_from_default_completion_config():
    settings = AIRequestSettings(service_id="test_service")
    chat_settings = OpenAIChatRequestSettings.from_ai_request(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature == 0.0
    assert chat_settings.top_p == 1.0
    assert chat_settings.presence_penalty == 0.0
    assert chat_settings.frequency_penalty == 0.0
    assert chat_settings.max_tokens == 256
    assert chat_settings.stop is None
    assert chat_settings.number_of_responses == 1
    assert chat_settings.logit_bias == {}


def test_openai_chat_request_settings_from_custom_completion_config():
    settings = AIRequestSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "stop": ["\n"],
            "number_of_responses": 2,
            "logprobs": 1,
            "logit_bias": {"1": 1},
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = OpenAIChatRequestSettings.from_ai_request(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop == ["\n"]
    assert chat_settings.number_of_responses == 2
    assert chat_settings.logit_bias == {"1": 1}


def test_create_options():
    settings = OpenAIChatRequestSettings(
        temperature=0.5,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=128,
        stop=["\n"],
        number_of_responses=2,
        logit_bias={"1": 1},
        messages=[{"role": "system", "content": "Hello"}],
    )
    options = settings.prepare_settings_dict()
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["presence_penalty"] == 0.5
    assert options["frequency_penalty"] == 0.5
    assert options["max_tokens"] == 128
    assert options["stop"] == ["\n"]
    assert options["n"] == 2
    assert options["logit_bias"] == {"1": 1}
    assert not options["stream"]
