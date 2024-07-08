# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
from numpy import array

from semantic_kernel.connectors.ai.ollama.services.ollama_text_embedding import OllamaTextEmbedding


@pytest.mark.asyncio
@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.embeddings")  # mock_embedding_client
async def test_custom_host(mock_embedding_client, mock_client, model_id, host, prompt):
    mock_embedding_client.return_value = {"embedding": [0.1, 0.2, 0.3]}

    ollama = OllamaTextEmbedding(ai_model_id=model_id, host=host)
    _ = await ollama.generate_embeddings(
        [prompt],
    )

    mock_client.assert_called_once_with(host=host)


@pytest.mark.asyncio
@patch("ollama.AsyncClient.embeddings")
async def test_embedding(mock_embedding_client, model_id, prompt):
    mock_embedding_client.return_value = {"embedding": [0.1, 0.2, 0.3]}

    ollama = OllamaTextEmbedding(ai_model_id=model_id)
    response = await ollama.generate_embeddings(
        [prompt],
    )
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_embedding_client.assert_called_once_with(model=model_id, prompt=prompt)
