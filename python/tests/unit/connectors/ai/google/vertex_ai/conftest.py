# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, AsyncIterable
from unittest.mock import MagicMock

import pytest
from google.cloud.aiplatform_v1beta1.types.content import Candidate, Content, Part
from google.cloud.aiplatform_v1beta1.types.prediction_service import GenerateContentResponse
from google.cloud.aiplatform_v1beta1.types.tool import FunctionCall
from vertexai.generative_models import GenerationResponse
from vertexai.language_models import TextEmbedding


@pytest.fixture()
def vertex_ai_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Vertex AI Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "VERTEX_AI_GEMINI_MODEL_ID": "test-gemini-model-id",
        "VERTEX_AI_EMBEDDING_MODEL_ID": "test-embedding-model-id",
        "VERTEX_AI_PROJECT_ID": "test-project-id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def mock_vertex_ai_chat_completion_response() -> GenerationResponse:
    """Mock Vertex AI Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[Part(text="Test content")])
    candidate.finish_reason = Candidate.FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return GenerationResponse._from_gapic(response)


@pytest.fixture()
def mock_vertex_ai_chat_completion_response_with_tool_call() -> GenerationResponse:
    """Mock Vertex AI Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(
        role="user",
        parts=[
            Part(
                function_call=FunctionCall(
                    name="test_function",
                    args={"test_arg": "test_value"},
                )
            )
        ],
    )
    candidate.finish_reason = Candidate.FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return GenerationResponse._from_gapic(response)


@pytest.fixture()
def mock_vertex_ai_streaming_chat_completion_response() -> AsyncIterable[GenerationResponse]:
    """Mock Vertex AI streaming Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(role="user", parts=[Part(text="Test content")])
    candidate.finish_reason = Candidate.FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [GenerationResponse._from_gapic(response)]

    return iterable


@pytest.fixture()
def mock_vertex_ai_streaming_chat_completion_response_with_tool_call() -> AsyncIterable[GenerationResponse]:
    """Mock Vertex AI streaming Chat Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(
        role="user",
        parts=[
            Part(
                function_call=FunctionCall(
                    name="getLightStatus",
                    args={"arg1": "test_value"},
                )
            )
        ],
    )
    candidate.finish_reason = Candidate.FinishReason.STOP

    response = GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [GenerationResponse._from_gapic(response)]

    return iterable


@pytest.fixture()
def mock_vertex_ai_text_completion_response() -> GenerationResponse:
    """Mock Vertex AI Text Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(parts=[Part(text="Test content")])

    response = GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    return GenerationResponse._from_gapic(response)


@pytest.fixture()
def mock_vertex_ai_streaming_text_completion_response() -> AsyncIterable[GenerationResponse]:
    """Mock Vertex AI streaming Text Completion response."""
    candidate = Candidate()
    candidate.index = 0
    candidate.content = Content(parts=[Part(text="Test content")])

    response = GenerateContentResponse()
    response.candidates.append(candidate)
    response.usage_metadata = GenerateContentResponse.UsageMetadata(
        prompt_token_count=0,
        candidates_token_count=0,
        total_token_count=0,
    )

    iterable = MagicMock(spec=AsyncGenerator)
    iterable.__aiter__.return_value = [GenerationResponse._from_gapic(response)]

    return iterable


class MockTextEmbeddingModel:
    async def get_embeddings_async(
        self,
        texts: list[str],
        *,
        auto_truncate: bool = True,
        output_dimensionality: int | None = None,
    ) -> list[TextEmbedding]:
        pass
