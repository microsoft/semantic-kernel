# Copyright (c) Microsoft. All rights reserved.

import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

if sys.version_info >= (3, 9):
    from semantic_kernel.connectors.ai.google_palm.services.gp_text_embedding import (
        GooglePalmTextEmbedding,
    )


pytestmark = pytest.mark.skipif(sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater")


def test_google_palm_text_embedding_init() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"

    # Test successful initialization
    gp_text_embed = GooglePalmTextEmbedding(
        ai_model_id=ai_model_id,
        api_key=api_key,
    )

    assert gp_text_embed.ai_model_id == ai_model_id
    assert gp_text_embed.api_key == api_key
    assert isinstance(gp_text_embed, GooglePalmTextEmbedding)


def test_google_palm_text_embedding_init_with_empty_api_key() -> None:
    ai_model_id = "test_model_id"
    # api_key = "test_api_key"

    with pytest.raises(ValidationError, match="api_key"):
        GooglePalmTextEmbedding(
            ai_model_id=ai_model_id,
            api_key="",
        )


@pytest.mark.asyncio
async def test_google_palm_text_embedding_calls_with_parameters() -> None:
    mock_gp = MagicMock()
    mock_gp.generate_embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
    with patch(
        "semantic_kernel.connectors.ai.google_palm.services.gp_text_embedding.palm",
        new=mock_gp,
    ):
        ai_model_id = "test_model_id"
        api_key = "test_api_key"
        texts = ["hello world"]
        text = "hello world"

        gp_text_embedding = GooglePalmTextEmbedding(
            ai_model_id=ai_model_id,
            api_key=api_key,
        )

        await gp_text_embedding.generate_embeddings(texts)

        mock_gp.generate_embeddings.assert_called_once_with(
            model=ai_model_id,
            text=text,
        )
