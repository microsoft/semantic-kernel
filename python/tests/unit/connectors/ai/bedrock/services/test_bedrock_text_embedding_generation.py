# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import ANY, Mock, patch

import boto3
import pytest

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import (
    BedrockEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.bedrock.services.bedrock_text_embedding import BedrockTextEmbedding
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidResponseError,
)
from tests.unit.connectors.ai.bedrock.conftest import MockBedrockClient, MockBedrockRuntimeClient

# region init


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_embedding_init(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service"""
    bedrock_text_embedding = BedrockTextEmbedding()

    assert bedrock_text_embedding.ai_model_id == bedrock_unit_test_env["BEDROCK_EMBEDDING_MODEL_ID"]
    assert bedrock_text_embedding.service_id == bedrock_unit_test_env["BEDROCK_EMBEDDING_MODEL_ID"]

    assert bedrock_text_embedding.bedrock_client is not None
    assert bedrock_text_embedding.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_embedding_init_model_id_override(mock_client, bedrock_unit_test_env, model_id) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service"""
    bedrock_text_embedding = BedrockTextEmbedding(model_id=model_id)

    assert bedrock_text_embedding.ai_model_id == model_id
    assert bedrock_text_embedding.service_id == model_id

    assert bedrock_text_embedding.bedrock_client is not None
    assert bedrock_text_embedding.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_embedding_init_custom_service_id(mock_client, bedrock_unit_test_env, service_id) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service"""
    bedrock_text_embedding = BedrockTextEmbedding(service_id=service_id)

    assert bedrock_text_embedding.service_id == service_id

    assert bedrock_text_embedding.bedrock_client is not None
    assert bedrock_text_embedding.bedrock_runtime_client is not None


def test_bedrock_text_embedding_init_custom_clients(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service"""
    bedrock_text_embedding = BedrockTextEmbedding(
        runtime_client=MockBedrockRuntimeClient(),
        client=MockBedrockClient(),
    )

    assert isinstance(bedrock_text_embedding.bedrock_client, MockBedrockClient)
    assert isinstance(bedrock_text_embedding.bedrock_runtime_client, MockBedrockRuntimeClient)


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_embedding_init_custom_client(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service"""
    bedrock_text_embedding = BedrockTextEmbedding(
        client=MockBedrockClient(),
    )

    assert isinstance(bedrock_text_embedding.bedrock_client, MockBedrockClient)
    assert bedrock_text_embedding.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_embedding_init_custom_runtime_client(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service"""
    bedrock_text_embedding = BedrockTextEmbedding(
        runtime_client=MockBedrockRuntimeClient(),
    )

    assert bedrock_text_embedding.bedrock_client is not None
    assert isinstance(bedrock_text_embedding.bedrock_runtime_client, MockBedrockRuntimeClient)


@pytest.mark.parametrize("exclude_list", [["BEDROCK_EMBEDDING_MODEL_ID"]], indirect=True)
def test_bedrock_text_embedding_client_init_with_empty_model_id(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service with empty model id"""
    with pytest.raises(ServiceInitializationError, match="The Amazon Bedrock Text Embedding Model ID is missing."):
        BedrockTextEmbedding(env_file_path="fake_env_file_path.env")


def test_bedrock_text_embedding_client_init_invalid_settings(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Embedding service with invalid settings"""
    with pytest.raises(
        ServiceInitializationError, match="Failed to initialize the Amazon Bedrock Text Embedding Service."
    ):
        BedrockTextEmbedding(model_id=123)  # Model ID must be a string


@patch.object(boto3, "client", return_value=Mock())
def test_prompt_execution_settings_class(mock_client, bedrock_unit_test_env) -> None:
    """Test getting prompt execution settings class"""
    bedrock_completion_client = BedrockTextEmbedding()
    assert bedrock_completion_client.get_prompt_execution_settings_class() == BedrockEmbeddingPromptExecutionSettings


# endregion


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
        "cohere.command",
    ],
    indirect=True,
)
async def test_bedrock_text_embedding(model_id, mock_bedrock_text_embedding_response) -> None:
    """Test Bedrock text embedding generation"""
    with patch.object(
        MockBedrockRuntimeClient, "invoke_model", return_value=mock_bedrock_text_embedding_response
    ) as mock_model_invoke:
        # Setup
        bedrock_text_embedding = BedrockTextEmbedding(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        # Act
        settings = BedrockEmbeddingPromptExecutionSettings()
        response = await bedrock_text_embedding.generate_embeddings(["hello", "world"], settings)

        # Assert
        mock_model_invoke.assert_called_with(
            body=ANY,
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
        )
        assert mock_model_invoke.call_count == 2

        assert len(response) == 2


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
        "cohere.command",
    ],
    indirect=True,
)
async def test_bedrock_text_embedding_with_invalid_response(
    model_id, mock_bedrock_text_embedding_invalid_response
) -> None:
    """Test Bedrock text embedding generation with invalid response"""
    with patch.object(
        MockBedrockRuntimeClient, "invoke_model", return_value=mock_bedrock_text_embedding_invalid_response
    ):
        # Setup
        bedrock_text_embedding = BedrockTextEmbedding(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        with pytest.raises(ServiceInvalidResponseError):
            await bedrock_text_embedding.generate_embeddings(["hello", "world"])
