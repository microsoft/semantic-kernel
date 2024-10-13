# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.google_palm.services.gp_text_embedding import (
    GooglePalmTextEmbedding,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_google_palm_text_embedding_init(google_palm_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    # Test successful initialization
    gp_text_embed = GooglePalmTextEmbedding(
        ai_model_id=ai_model_id,
    )

    assert gp_text_embed.ai_model_id == ai_model_id
    assert gp_text_embed.api_key == google_palm_unit_test_env["GOOGLE_PALM_API_KEY"]
    assert isinstance(gp_text_embed, GooglePalmTextEmbedding)


@pytest.mark.parametrize("exclude_list", [["GOOGLE_PALM_API_KEY"]], indirect=True)
def test_google_palm_text_embedding_init_with_empty_api_key(google_palm_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        GooglePalmTextEmbedding(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


@pytest.mark.asyncio
async def test_google_palm_text_embedding_calls_with_parameters(google_palm_unit_test_env) -> None:
    mock_gp = MagicMock()
    mock_gp.generate_embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
    with patch(
        "semantic_kernel.connectors.ai.google_palm.services.gp_text_embedding.palm",
        new=mock_gp,
    ):
        ai_model_id = "test_model_id"
        texts = ["hello world"]
        text = "hello world"

        gp_text_embedding = GooglePalmTextEmbedding(
            ai_model_id=ai_model_id,
        )

        await gp_text_embedding.generate_embeddings(texts)

        mock_gp.generate_embeddings.assert_called_once_with(
            model=ai_model_id,
            text=text,
        )
