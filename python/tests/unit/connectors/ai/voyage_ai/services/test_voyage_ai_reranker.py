# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.connectors.ai.reranker_base import RerankResult
from semantic_kernel.connectors.ai.voyage_ai import VoyageAIReranker, VoyageAIRerankPromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException


def test_init(voyage_ai_unit_test_env):
    """Test VoyageAI reranker initialization."""
    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    assert reranker_service.ai_model_id == "rerank-2.5"
    assert reranker_service.service_id == "rerank-2.5"
    assert reranker_service.aclient is not None


def test_init_from_env(voyage_ai_unit_test_env):
    """Test initialization from environment variables."""
    reranker_service = VoyageAIReranker()

    assert reranker_service.ai_model_id == "rerank-2.5"


def test_init_with_custom_endpoint(voyage_ai_unit_test_env):
    """Test initialization with custom endpoint."""
    custom_endpoint = "https://custom-endpoint.com/v1"
    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
        endpoint=custom_endpoint,
    )

    assert reranker_service.endpoint == custom_endpoint


def test_prompt_execution_settings_class():
    """Test getting prompt execution settings class."""
    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    assert reranker_service.get_prompt_execution_settings_class() == VoyageAIRerankPromptExecutionSettings


@pytest.mark.asyncio
async def test_rerank(voyage_ai_unit_test_env):
    """Test reranking documents."""
    # Mock response
    mock_result_1 = MagicMock()
    mock_result_1.index = 2
    mock_result_1.document = "Most relevant doc"
    mock_result_1.relevance_score = 0.95

    mock_result_2 = MagicMock()
    mock_result_2.index = 0
    mock_result_2.document = "Somewhat relevant doc"
    mock_result_2.relevance_score = 0.75

    mock_response = MagicMock()
    mock_response.results = [mock_result_1, mock_result_2]

    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    # Mock the aclient
    reranker_service._aclient.rerank = AsyncMock(return_value=mock_response)

    query = "What is Semantic Kernel?"
    documents = [
        "Somewhat relevant doc",
        "Irrelevant doc",
        "Most relevant doc",
    ]

    results = await reranker_service.rerank(query, documents)

    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(r, RerankResult) for r in results)
    assert results[0].index == 2
    assert results[0].relevance_score == 0.95
    assert results[1].index == 0
    assert results[1].relevance_score == 0.75
    reranker_service._aclient.rerank.assert_called_once()


@pytest.mark.asyncio
async def test_rerank_with_settings(voyage_ai_unit_test_env):
    """Test reranking with execution settings."""
    # Mock response
    mock_result = MagicMock()
    mock_result.index = 0
    mock_result.document = "Top result"
    mock_result.relevance_score = 0.95

    mock_response = MagicMock()
    mock_response.results = [mock_result]

    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    # Mock the aclient
    reranker_service._aclient.rerank = AsyncMock(return_value=mock_response)

    settings = VoyageAIRerankPromptExecutionSettings(
        top_k=1,  # Only return top result
        truncation=True,
    )

    query = "test query"
    documents = ["doc1", "doc2", "doc3"]

    results = await reranker_service.rerank(query, documents, settings=settings)

    assert len(results) == 1
    assert results[0].relevance_score == 0.95
    reranker_service._aclient.rerank.assert_called_once()


@pytest.mark.asyncio
async def test_rerank_empty_results(voyage_ai_unit_test_env):
    """Test reranking with empty results."""
    mock_response = MagicMock()
    mock_response.results = []

    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    # Mock the aclient
    reranker_service._aclient.rerank = AsyncMock(return_value=mock_response)

    query = "test query"
    documents = ["doc1"]

    results = await reranker_service.rerank(query, documents)

    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_rerank_failure(voyage_ai_unit_test_env):
    """Test handling of reranking failure."""
    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    # Mock the aclient to raise an exception
    reranker_service._aclient.rerank = AsyncMock(side_effect=Exception("API error"))

    query = "test query"
    documents = ["doc1", "doc2"]

    with pytest.raises(ServiceResponseException):
        await reranker_service.rerank(query, documents)


def test_service_url():
    """Test service URL retrieval."""
    reranker_service = VoyageAIReranker(
        ai_model_id="rerank-2.5",
        api_key="test-api-key",
    )

    assert reranker_service.service_url() == "https://api.voyageai.com/v1"
