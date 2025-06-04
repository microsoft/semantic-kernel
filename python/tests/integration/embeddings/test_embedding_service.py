# Copyright (c) Microsoft. All rights reserved.


from typing import Any

import pytest

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from tests.integration.embeddings.test_embedding_service_base import (
    EmbeddingServiceTestBase,
    google_ai_setup,
    mistral_ai_setup,
    ollama_setup,
    vertex_ai_setup,
)

pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, output_dimensionality",
    [
        pytest.param(
            "openai",
            {},
            1536,  # text-embedding-ada-002 doesn't support custom output dimensionality
            id="openai",
        ),
        pytest.param(
            "azure",
            {},
            1536,  # text-embedding-ada-002 doesn't support custom output dimensionality
            id="azure",
        ),
        pytest.param(
            "azure_custom_client",
            {},
            1536,  # text-embedding-ada-002 doesn't support custom output dimensionality
            id="azure_custom_client",
        ),
        pytest.param(
            "azure_ai_inference",
            {},
            1536,  # text-embedding-ada-002 doesn't support custom output dimensionality
            id="azure_ai_inference",
        ),
        pytest.param(
            "mistral_ai",
            {},
            1024,
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI environment variables not set"),
            id="mistral_ai",
        ),
        pytest.param(
            "hugging_face",
            {},
            384,
            id="hugging_face",
        ),
        pytest.param(
            "ollama",
            {},
            768,
            marks=(
                pytest.mark.skipif(not ollama_setup, reason="Ollama not setup"),
                pytest.mark.ollama,
            ),
            id="ollama",
        ),
        pytest.param(
            "google_ai",
            {"output_dimensionality": 10},
            10,
            marks=pytest.mark.skipif(not google_ai_setup, reason="Google AI environment variables not set"),
            id="google_ai",
        ),
        pytest.param(
            "vertex_ai",
            {"output_dimensionality": 10},
            10,
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI environment variables not set"),
            id="vertex_ai",
        ),
        pytest.param(
            "bedrock_amazon_titan-v1",
            {},
            1536,  # This model doesn't support custom output dimensionality
            id="bedrock_amazon_titan-v1",
        ),
        pytest.param(
            "bedrock_amazon_titan-v2",
            {"extension_data": {"dimensions": 256}},
            256,
            id="bedrock_amazon_titan-v2",
        ),
        pytest.param(
            "bedrock_cohere",
            {},
            1024,
            id="bedrock_cohere",
        ),
    ],
)


class TestEmbeddingService(EmbeddingServiceTestBase):
    """Test embedding service with memory.

    This tests if the embedding service can be used with the semantic memory.
    """

    async def test_embedding_service(
        self,
        service_id,
        services: dict[str, tuple[EmbeddingGeneratorBase, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        output_dimensionality: int,
    ):
        embedding_generator, settings_type = services[service_id]
        embeddings = await embedding_generator.generate_embeddings(
            texts=["Hello, world!", "Hello, universe!"],
            settings=settings_type(**execution_settings_kwargs),
        )

        assert embeddings.shape == (2, output_dimensionality)
