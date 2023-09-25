# Copyright (c) Microsoft. All rights reserved.

import json

import pytest

from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)


def test_default_prompt_template_config():
    prompt_template_config = PromptTemplateConfig()
    assert prompt_template_config.schema == 1
    assert prompt_template_config.type == "completion"
    assert prompt_template_config.description == ""
    assert prompt_template_config.completion.temperature == 0.0
    assert prompt_template_config.completion.top_p == 1.0
    assert prompt_template_config.completion.presence_penalty == 0.0
    assert prompt_template_config.completion.frequency_penalty == 0.0
    assert prompt_template_config.completion.max_tokens == 256
    assert prompt_template_config.completion.number_of_responses == 1
    assert prompt_template_config.completion.stop_sequences == []
    assert prompt_template_config.completion.token_selection_biases == {}
    assert prompt_template_config.completion.chat_system_prompt is None


def test_default_chat_prompt_template_from_empty_dict():
    with pytest.raises(KeyError):
        _ = PromptTemplateConfig().from_dict({})


def test_default_chat_prompt_template_from_empty_string():
    with pytest.raises(json.decoder.JSONDecodeError):
        _ = PromptTemplateConfig().from_json("")


def test_default_chat_prompt_template_from_empty_json():
    with pytest.raises(KeyError):
        _ = PromptTemplateConfig().from_json("{}")


def test_custom_prompt_template_config():
    prompt_template_config = PromptTemplateConfig(
        schema=2,
        type="completion2",
        description="Custom description.",
        completion=PromptTemplateConfig.CompletionConfig(
            temperature=0.5,
            top_p=0.5,
            presence_penalty=0.5,
            frequency_penalty=0.5,
            max_tokens=128,
            number_of_responses=2,
            stop_sequences=["\n"],
            token_selection_biases={1: 1},
            chat_system_prompt="Custom system prompt.",
        ),
    )
    assert prompt_template_config.schema == 2
    assert prompt_template_config.type == "completion2"
    assert prompt_template_config.description == "Custom description."
    assert prompt_template_config.completion.temperature == 0.5
    assert prompt_template_config.completion.top_p == 0.5
    assert prompt_template_config.completion.presence_penalty == 0.5
    assert prompt_template_config.completion.frequency_penalty == 0.5
    assert prompt_template_config.completion.max_tokens == 128
    assert prompt_template_config.completion.number_of_responses == 2
    assert prompt_template_config.completion.stop_sequences == ["\n"]
    assert prompt_template_config.completion.token_selection_biases == {1: 1}
    assert (
        prompt_template_config.completion.chat_system_prompt == "Custom system prompt."
    )


def test_custom_prompt_template_config_from_dict():
    prompt_template_dict = {
        "schema": 2,
        "type": "completion2",
        "description": "Custom description.",
        "completion": {
            "temperature": 0.5,
            "top_p": 0.5,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "number_of_responses": 2,
            "stop_sequences": ["\n"],
            "token_selection_biases": {1: 1},
            "chat_system_prompt": "Custom system prompt.",
        },
    }
    prompt_template_config = PromptTemplateConfig().from_dict(prompt_template_dict)
    assert prompt_template_config.schema == 2
    assert prompt_template_config.type == "completion2"
    assert prompt_template_config.description == "Custom description."
    assert prompt_template_config.completion.temperature == 0.5
    assert prompt_template_config.completion.top_p == 0.5
    assert prompt_template_config.completion.presence_penalty == 0.5
    assert prompt_template_config.completion.frequency_penalty == 0.5
    assert prompt_template_config.completion.max_tokens == 128
    assert prompt_template_config.completion.number_of_responses == 2
    assert prompt_template_config.completion.stop_sequences == ["\n"]
    assert prompt_template_config.completion.token_selection_biases == {1: 1}
    assert (
        prompt_template_config.completion.chat_system_prompt == "Custom system prompt."
    )


def test_custom_prompt_template_config_from_json():
    prompt_template_json = """
    {
        "schema": 2,
        "type": "completion2",
        "description": "Custom description.",
        "completion": {
            "temperature": 0.5,
            "top_p": 0.5,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "number_of_responses": 2,
            "stop_sequences": ["s"],
            "token_selection_biases": {"1": 1},
            "chat_system_prompt": "Custom system prompt."
        }
    }
    """
    prompt_template_config = PromptTemplateConfig().from_json(prompt_template_json)
    assert prompt_template_config.schema == 2
    assert prompt_template_config.type == "completion2"
    assert prompt_template_config.description == "Custom description."
    assert prompt_template_config.completion.temperature == 0.5
    assert prompt_template_config.completion.top_p == 0.5
    assert prompt_template_config.completion.presence_penalty == 0.5
    assert prompt_template_config.completion.frequency_penalty == 0.5
    assert prompt_template_config.completion.max_tokens == 128
    assert prompt_template_config.completion.number_of_responses == 2
    assert prompt_template_config.completion.stop_sequences == ["s"]
    assert prompt_template_config.completion.token_selection_biases == {1: 1}
    assert (
        prompt_template_config.completion.chat_system_prompt == "Custom system prompt."
    )


def test_chat_prompt_template():
    chat_prompt_template = ChatPromptTemplate(
        "{{$user_input}}",
        None,
        prompt_config=PromptTemplateConfig(),
    )

    assert chat_prompt_template._messages == []


def test_chat_prompt_template_with_system_prompt():
    prompt_template_config = PromptTemplateConfig(
        completion=PromptTemplateConfig.CompletionConfig(
            chat_system_prompt="Custom system prompt.",
        )
    )

    chat_prompt_template = ChatPromptTemplate(
        "{{$user_input}}",
        None,
        prompt_config=prompt_template_config,
    )

    print(chat_prompt_template.messages)
    assert len(chat_prompt_template.messages) == 1
    assert chat_prompt_template.messages[0]["role"] == "system"
    assert chat_prompt_template.messages[0]["content"] == "Custom system prompt."
