# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import Mock

import pytest

from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import BedrockModelProvider
from semantic_kernel.contents.chat_history import ChatHistory


@pytest.fixture()
def model_id(request) -> str:
    if hasattr(request, "param"):
        return request.param
    return "test_model_id"


@pytest.fixture()
def service_id() -> str:
    return "test_service_id"


@pytest.fixture()
def chat_history() -> ChatHistory:
    chat_history = ChatHistory(system_message="You are a helpful assistant.")

    chat_history.add_user_message("Hello!")
    chat_history.add_assistant_message("Hi! How can I help you today?")
    chat_history.add_system_message("Be polite and respectful.")
    chat_history.add_user_message("I need help with a task.")

    return chat_history


@pytest.fixture()
def bedrock_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Amazon Bedrock AI connector unit tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "BEDROCK_TEXT_MODEL_ID": "env_test_text_model_id",
        "BEDROCK_CHAT_MODEL_ID": "env_test_chat_model_id",
        "BEDROCK_EMBEDDING_MODEL_ID": "env_test_embedding_model_id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


class MockBedrockClient(Mock):
    def __init__(self, *args, **kwargs):
        pass

    def get_foundation_model(self, *args, **kwargs):
        return {
            "modelDetails": {
                "responseStreamingSupported": True,
                "inputModalities": ["TEXT"],
                "outputModalities": ["TEXT", "EMBEDDING"],
            }
        }


class MockBedrockRuntimeClient(Mock):
    def __init__(self, *args, **kwargs):
        pass

    def converse(self, *args, **kwargs):
        pass

    def converse_stream(self, *args, **kwargs):
        pass

    def invoke_model(self, *args, **kwargs):
        pass

    def invoke_model_with_response_stream(self, *args, **kwargs):
        pass


# region mock chat completion responses


@pytest.fixture()
def mock_bedrock_chat_completion_response():
    # https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-call.html#conversation-inference-call-response
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "text": "Hi! How can I help you today?",
                    }
                ],
            }
        },
        "stopReason": "end_turn",
        "usage": {
            "inputTokens": 125,
            "outputTokens": 60,
            "totalTokens": 185,
        },
    }


@pytest.fixture()
def mock_bedrock_streaming_chat_completion_response():
    # https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-call.html#conversation-inference-call-response
    events = [
        {"messageStart": {"role": "assistant"}},
        {"contentBlockStart": {"contentBlockIndex": 0, "start": {}}},
        {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "Hi! "}}},
        {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "How can "}}},
        {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "I help you today?"}}},
        {"contentBlockStop": {"contentBlockIndex": 0}},
        {"messageStop": {"stopReason": "end_turn"}},
        {
            "metadata": {
                "metrics": {"latencyMs": 1000},
                "usage": {"inputTokens": 125, "outputTokens": 60, "totalTokens": 185},
            }
        },
    ]

    def event_stream(events):
        yield from events

    return {"stream": event_stream(events)}


@pytest.fixture()
def mock_bedrock_streaming_chat_completion_invalid_response():
    events = [
        {"unknown": {}},
    ]

    def event_stream(events):
        yield from events

    return {"stream": event_stream(events)}


# endregion

# region mock text completion responses


@pytest.fixture()
def output_text():
    return "Hi! How can I help you today?"


@pytest.fixture()
def mock_bedrock_text_completion_response(model_id: str, output_text: str):
    model_provider = BedrockModelProvider.to_model_provider(model_id)

    match model_provider:
        case BedrockModelProvider.AMAZON:
            body = {
                "inputTextTokenCount": 10,
                "results": [
                    {
                        "tokenCount": 10,
                        "outputText": output_text,
                        "completionReason": "FINISHED ",
                    }
                ],
            }
        case BedrockModelProvider.ANTHROPIC:
            body = {
                "completion": output_text,
                "stop_reason": "stop_sequence",
                "stop": "",
            }
        case BedrockModelProvider.COHERE:
            body = {
                "generations": [
                    {
                        "text": output_text,
                    }
                ],
            }
        case BedrockModelProvider.AI21LABS:
            body = {
                "completions": [
                    {
                        "data": {
                            "text": output_text,
                        }
                    }
                ],
            }
        case BedrockModelProvider.META:
            body = {
                "generation": output_text,
                "prompt_token_count": 10,
                "generation_token_count": 10,
            }
        case BedrockModelProvider.MISTRALAI:
            body = {"outputs": [{"text": output_text}]}

    mock = Mock()
    mock.read.return_value = json.dumps(body)

    return {"body": mock}


@pytest.fixture()
def mock_bedrock_streaming_text_completion_response(model_id: str, output_text: str):
    model_provider = BedrockModelProvider.to_model_provider(model_id)

    match model_provider:
        case BedrockModelProvider.AMAZON:
            chunks = [
                {
                    "chunk": {
                        "bytes": json.dumps({
                            "inputTextTokenCount": 10,
                            "totalOutputTextTokenCount": 10,
                            "outputText": chunk,
                        }).encode(),
                    }
                }
                for chunk in [output_text[i : i + 3] for i in range(0, len(output_text), 3)]
            ]

    def event_stream(events):
        yield from events

    return {"body": event_stream(chunks)}


# endregion


# region mock text embedding responses


@pytest.fixture()
def mock_bedrock_text_embedding_response(model_id: str):
    model_provider = BedrockModelProvider.to_model_provider(model_id)

    match model_provider:
        case BedrockModelProvider.AMAZON:
            body = {
                "embedding": [0.1, 0.2, 0.3],
            }
        case BedrockModelProvider.COHERE:
            body = {
                "embeddings": [[0.1, 0.2, 0.3]],
            }

    mock = Mock()
    mock.read.return_value = json.dumps(body)

    return {"body": mock}


@pytest.fixture()
def mock_bedrock_text_embedding_invalid_response(model_id: str):
    model_provider = BedrockModelProvider.to_model_provider(model_id)

    match model_provider:
        case BedrockModelProvider.AMAZON:
            body = {"embedding": 0.1}
        case BedrockModelProvider.COHERE:
            body = {"embeddings": 0.1}

    mock = Mock()
    mock.read.return_value = json.dumps(body)

    return {"body": mock}


# endregion
