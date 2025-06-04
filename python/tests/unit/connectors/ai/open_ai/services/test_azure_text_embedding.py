# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, call, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.embeddings import AsyncEmbeddings

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_azure_text_embedding_init(azure_openai_unit_test_env) -> None:
    # Test successful initialization
    azure_text_embedding = AzureTextEmbedding()

    assert azure_text_embedding.client is not None
    assert isinstance(azure_text_embedding.client, AsyncAzureOpenAI)
    assert azure_text_embedding.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]
    assert isinstance(azure_text_embedding, EmbeddingGeneratorBase)


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_text_embedding_init_with_empty_deployment_name(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextEmbedding(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_azure_text_embedding_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextEmbedding(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
def test_azure_text_embedding_init_with_invalid_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextEmbedding()


@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"AZURE_OPENAI_BASE_URL": "https://test_embedding_deployment.test-base-url.com"}],
    indirect=True,
)
def test_azure_text_embedding_init_with_from_dict(azure_openai_unit_test_env) -> None:
    default_headers = {"test_header": "test_value"}

    settings = {
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
        "endpoint": azure_openai_unit_test_env["AZURE_OPENAI_ENDPOINT"],
        "api_key": azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"],
        "api_version": azure_openai_unit_test_env["AZURE_OPENAI_API_VERSION"],
        "default_headers": default_headers,
    }

    azure_text_embedding = AzureTextEmbedding.from_dict(settings=settings)

    assert azure_text_embedding.client is not None
    assert isinstance(azure_text_embedding.client, AsyncAzureOpenAI)
    assert azure_text_embedding.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]
    assert isinstance(azure_text_embedding, EmbeddingGeneratorBase)
    assert settings["deployment_name"] in str(azure_text_embedding.client.base_url)
    assert azure_text_embedding.client.api_key == azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"]

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in azure_text_embedding.client.default_headers
        assert azure_text_embedding.client.default_headers[key] == value


def test_azure_text_embedding_generates_no_token_with_api_key_in_env(azure_openai_unit_test_env) -> None:
    with (
        patch(
            "semantic_kernel.utils.authentication.entra_id_authentication.get_entra_auth_token",
        ) as mock_get_token,
    ):
        azure_text_embedding = AzureTextEmbedding()

        assert azure_text_embedding.client is not None
        # API key is provided in env var, so the ad_token should be None
        assert mock_get_token.call_count == 0


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_azure_text_embedding_calls_with_parameters(mock_create, azure_openai_unit_test_env) -> None:
    texts = ["hello world", "goodbye world"]
    embedding_dimensions = 1536

    azure_text_embedding = AzureTextEmbedding()

    await azure_text_embedding.generate_embeddings(texts, dimensions=embedding_dimensions)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=azure_openai_unit_test_env["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
        dimensions=embedding_dimensions,
    )


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_azure_text_embedding_calls_with_batches(mock_create, azure_openai_unit_test_env) -> None:
    texts = [i for i in range(0, 5)]

    azure_text_embedding = AzureTextEmbedding()

    await azure_text_embedding.generate_embeddings(texts, batch_size=3)

    mock_create.assert_has_awaits(
        [
            call(
                model=azure_openai_unit_test_env["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
                input=texts[0:3],
            ),
            call(
                model=azure_openai_unit_test_env["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
                input=texts[3:5],
            ),
        ],
        any_order=False,
    )
