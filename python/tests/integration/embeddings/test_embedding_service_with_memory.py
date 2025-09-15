# Copyright (c) Microsoft. All rights reserved.


from typing import Any

import pytest

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore
from tests.integration.embeddings.test_embedding_service_base import (
    EmbeddingServiceTestBase,
    google_ai_setup,
    mistral_ai_setup,
    ollama_setup,
    vertex_ai_setup,
)

pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs",
    [
        pytest.param(
            "openai",
            {},
            id="openai",
        ),
        pytest.param(
            "azure",
            {},
            id="azure",
        ),
        pytest.param(
            "azure_custom_client",
            {},
            id="azure_custom_client",
        ),
        pytest.param(
            "azure_ai_inference",
            {},
            id="azure_ai_inference",
        ),
        pytest.param(
            "mistral_ai",
            {},
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI environment variables not set"),
            id="mistral_ai",
        ),
        pytest.param(
            "hugging_face",
            {},
            id="hugging_face",
        ),
        pytest.param(
            "ollama",
            {},
            marks=(
                pytest.mark.skipif(not ollama_setup, reason="Ollama environment variables not set"),
                pytest.mark.ollama,
            ),
            id="ollama",
        ),
        pytest.param(
            "google_ai",
            {},
            marks=pytest.mark.skipif(not google_ai_setup, reason="Google AI environment variables not set"),
            id="google_ai",
        ),
        pytest.param(
            "vertex_ai",
            {},
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI environment variables not set"),
            id="vertex_ai",
        ),
        pytest.param(
            "bedrock_amazon_titan-v1",
            {},
            id="bedrock_amazon_titan-v1",
        ),
        pytest.param(
            "bedrock_amazon_titan-v2",
            {},
            marks=pytest.mark.skip(reason="This is known to fail to get the correct answer for 'What are birds?'"),
            id="bedrock_amazon_titan-v2",
        ),
        pytest.param(
            "bedrock_cohere",
            {},
            id="bedrock_cohere",
        ),
    ],
)


class TestEmbeddingServiceWithMemory(EmbeddingServiceTestBase):
    """Test embedding service with memory.

    This tests if the embedding service can be used with the semantic memory.
    """

    async def test_embedding_service(
        self,
        service_id,
        services: dict[str, tuple[EmbeddingGeneratorBase, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
    ):
        embedding_generator, settings_type = services[service_id]

        if embedding_generator is None:
            pytest.skip(f"Service {service_id} not set up")

        memory = SemanticTextMemory(
            storage=VolatileMemoryStore(),
            embeddings_generator=embedding_generator,
        )

        # Add some documents to the semantic memory
        embeddings_kwargs = {"settings": settings_type(**execution_settings_kwargs)}
        await memory.save_information(
            "test",
            id="info1",
            text="Sharks are fish.",
            embeddings_kwargs=embeddings_kwargs,
        )
        await memory.save_information(
            "test",
            id="info2",
            text="Whales are mammals.",
            embeddings_kwargs=embeddings_kwargs,
        )
        await memory.save_information(
            "test",
            id="info3",
            text="Penguins are birds.",
            embeddings_kwargs=embeddings_kwargs,
        )
        await memory.save_information(
            "test",
            id="info4",
            text="Dolphins are mammals.",
            embeddings_kwargs=embeddings_kwargs,
        )
        await memory.save_information(
            "test",
            id="info5",
            text="Flies are insects.",
            embeddings_kwargs=embeddings_kwargs,
        )

        # Search for documents
        query = "What are mammals?"
        result = await memory.search("test", query, limit=2, min_relevance_score=0.0)
        assert "mammals." in result[0].text
        assert "mammals." in result[1].text

        query = "What are fish?"
        result = await memory.search("test", query, limit=1, min_relevance_score=0.0)
        assert result[0].text == "Sharks are fish."

        query = "What are insects?"
        result = await memory.search("test", query, limit=1, min_relevance_score=0.0)
        assert result[0].text == "Flies are insects."

        query = "What are birds?"
        result = await memory.search("test", query, limit=1, min_relevance_score=0.0)
        assert result[0].text == "Penguins are birds."
