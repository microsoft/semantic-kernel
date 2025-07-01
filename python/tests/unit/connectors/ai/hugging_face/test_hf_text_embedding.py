# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
from numpy import array, ndarray

from semantic_kernel.connectors.ai.hugging_face.services.hf_text_embedding import HuggingFaceTextEmbedding
from semantic_kernel.exceptions import ServiceResponseException


def test_huggingface_text_embedding_initialization():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    device = -1

    with patch("sentence_transformers.SentenceTransformer") as mock_transformer:
        mock_instance = mock_transformer.return_value
        service = HuggingFaceTextEmbedding(service_id="test", ai_model_id=model_name, device=device)

        assert service.ai_model_id == model_name
        assert service.device == "cpu"
        assert service.generator == mock_instance
        mock_transformer.assert_called_once_with(model_name_or_path=model_name, device="cpu")


async def test_generate_embeddings_success():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    device = -1
    texts = ["Hello world!", "How are you?"]
    mock_embeddings = array([[0.1, 0.2], [0.3, 0.4]])

    with patch("sentence_transformers.SentenceTransformer") as mock_transformer:
        mock_instance = mock_transformer.return_value
        mock_instance.encode.return_value = mock_embeddings

        service = HuggingFaceTextEmbedding(service_id="test", ai_model_id=model_name, device=device)
        embeddings = await service.generate_embeddings(texts)

        assert isinstance(embeddings, ndarray)
        assert embeddings.shape == (2, 2)
        assert (embeddings == mock_embeddings).all()


async def test_generate_embeddings_throws():
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    device = -1
    texts = ["Hello world!", "How are you?"]

    with patch("sentence_transformers.SentenceTransformer") as mock_transformer:
        mock_instance = mock_transformer.return_value
        mock_instance.encode.side_effect = Exception("Test exception")

        service = HuggingFaceTextEmbedding(service_id="test", ai_model_id=model_name, device=device)

        with pytest.raises(ServiceResponseException, match="Hugging Face embeddings failed"):
            await service.generate_embeddings(texts)
