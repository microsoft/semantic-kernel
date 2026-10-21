# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from google.genai.types import (
    Candidate,
    Content,
    FinishReason,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
    Part,
)


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
        "GOOGLE_AI_CLOUD_PROJECT_ID": "test-project-id",
        "GOOGLE_AI_CLOUD_REGION": "test-region",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def mock_google_ai_chat_completion_response() -> GenerateContentResponse:
    """Mock Google AI Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[Part.from_text(text="Test content")])
    candidate.finish_reason = FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return response


@pytest.fixture()
def mock_google_ai_chat_completion_response_with_tool_call() -> GenerateContentResponse:
    """Mock Google AI Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(
        role="user",
        parts=[
            Part.from_function_call(
                name="test_function",
                args={"test_arg": "test_value"},
            )
        ],
    )
    candidate.finish_reason = FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return response


@pytest_asyncio.fixture
async def mock_google_ai_streaming_chat_completion_response() -> AsyncIterator[GenerateContentResponse]:
    """Mock Google AI streaming Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[Part.from_text(text="Test content")])
    candidate.finish_reason = FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [response]

    return iterable


@pytest_asyncio.fixture
async def mock_google_ai_streaming_chat_completion_response_with_tool_call() -> AsyncIterator[GenerateContentResponse]:
    """Mock Google AI streaming Chat Completion response with tool call."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(
        role="user",
        parts=[
            Part.from_function_call(
                name="getLightStatus",
                args={"arg1": "test_value"},
            )
        ],
    )
    candidate.finish_reason = FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates = [candidate]
    response.usage_metadata = GenerateContentResponseUsageMetadata(
        prompt_token_count=0,
        cached_content_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [response]

    return iterable


@pytest.fixture()
def mock_google_ai_text_completion_response() -> GenerateContentResponse:
    """Mock Google AI Text Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(parts=[Part.from_text(text="Test content")])

    response = GenerateContentResponse()
    response.candidates = [candidate]

    return response


@pytest_asyncio.fixture
async def mock_google_ai_streaming_text_completion_response() -> AsyncIterator[GenerateContentResponse]:
    """Mock Google AI streaming Text Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(parts=[Part.from_text(text="Test content")])

    response = GenerateContentResponse()
    response.candidates = [candidate]

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [response]

    return iterable
