# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai.resources.embeddings import AsyncEmbeddings

from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding


@pytest.mark.asyncio
@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_openai_text_embedding_calls_with_parameters(mock_create, openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]
    embedding_dimensions = 1536

    openai_text_embedding = OpenAITextEmbedding(
        ai_model_id=ai_model_id,
    )

    await openai_text_embedding.generate_embeddings(texts, dimensions=embedding_dimensions)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        dimensions=embedding_dimensions,
    )
