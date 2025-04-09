# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from google.generativeai import protos
from google.generativeai.types import AsyncGenerateContentResponse


@pytest.fixture()
def google_ai_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Google AI Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "GOOGLE_AI_GEMINI_MODEL_ID": "test-gemini-model-id",
        "GOOGLE_AI_EMBEDDING_MODEL_ID": "test-embedding-model-id",
        "GOOGLE_AI_API_KEY": "test-api-key",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def mock_google_ai_chat_completion_response() -> AsyncGenerateContentResponse:
    """Mock Google AI Chat Completion response."""
    candidate = protos.Candidate()
    candidate.index = 0
    candidate.content = protos.Content(role="user", parts=[protos.Part(text="Test content")])
    candidate.finish_reason = protos.Candidate.FinishReason.STOP

    response = protos.GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = protos.GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return AsyncGenerateContentResponse(
        done=True,
        iterator=None,
        result=response,
    )


@pytest.fixture()
def mock_google_ai_chat_completion_response_with_tool_call() -> AsyncGenerateContentResponse:
    """Mock Google AI Chat Completion response."""
    candidate = protos.Candidate()
    candidate.index = 0
    candidate.content = protos.Content(
        role="user",
        parts=[
            protos.Part(
                function_call=protos.FunctionCall(
                    name="test_function",
                    args={"test_arg": "test_value"},
                )
            )
        ],
    )
    candidate.finish_reason = protos.Candidate.FinishReason.STOP

    response = protos.GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = protos.GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return AsyncGenerateContentResponse(
        done=True,
        iterator=None,
        result=response,
    )


@pytest_asyncio.fixture
async def mock_google_ai_streaming_chat_completion_response() -> AsyncGenerateContentResponse:
    """Mock Google AI streaming Chat Completion response."""
    candidate = protos.Candidate()
    candidate.index = 0
    candidate.content = protos.Content(role="user", parts=[protos.Part(text="Test content")])
    candidate.finish_reason = protos.Candidate.FinishReason.STOP

    response = protos.GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = protos.GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [response]

    return await AsyncGenerateContentResponse.from_aiterator(
        iterator=iterable,
    )


@pytest_asyncio.fixture
async def mock_google_ai_streaming_chat_completion_response_with_tool_call() -> AsyncGenerateContentResponse:
    """Mock Google AI streaming Chat Completion response with tool call."""
    candidate = protos.Candidate()
    candidate.index = 0
    candidate.content = protos.Content(
        role="user",
        parts=[
            protos.Part(
                function_call=protos.FunctionCall(
                    name="getLightStatus",
                    args={"arg1": "test_value"},
                )
            )
        ],
    )
    candidate.finish_reason = protos.Candidate.FinishReason.STOP

    response = protos.GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = protos.GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [response]

    return await AsyncGenerateContentResponse.from_aiterator(
        iterator=iterable,
    )


@pytest.fixture()
def mock_google_ai_text_completion_response() -> AsyncGenerateContentResponse:
    """Mock Google AI Text Completion response."""
    candidate = protos.Candidate()
    candidate.index = 0
    candidate.content = protos.Content(parts=[protos.Part(text="Test content")])

    response = protos.GenerateContentResponse()
    response.candidates.append(candidate)

    return AsyncGenerateContentResponse(
        done=True,
        iterator=None,
        result=response,
    )


@pytest_asyncio.fixture
async def mock_google_ai_streaming_text_completion_response() -> AsyncGenerateContentResponse:
    """Mock Google AI streaming Text Completion response."""
    candidate = protos.Candidate()
    candidate.index = 0
    candidate.content = protos.Content(parts=[protos.Part(text="Test content")])

    response = protos.GenerateContentResponse()
    response.candidates.append(candidate)

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [response]

    return await AsyncGenerateContentResponse.from_aiterator(
        iterator=iterable,
    )
