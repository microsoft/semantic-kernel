# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, call, patch

import pytest
from openai.resources.embeddings import AsyncEmbeddings
from pydantic import ValidationError

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


@pytest.mark.asyncio
@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_openai_text_embedding_calls_with_parameters(mock_create) -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    texts = ["hello world", "goodbye world"]
    embedding_kwargs = {"dimensions": 1536}

    openai_text_embedding = OpenAITextEmbedding(
        ai_model_id=ai_model_id,
        api_key=api_key,
    )

    await openai_text_embedding.generate_embeddings(texts, **embedding_kwargs)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        **embedding_kwargs
    )
