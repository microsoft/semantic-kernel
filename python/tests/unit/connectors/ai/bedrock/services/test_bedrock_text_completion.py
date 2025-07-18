# Copyright (c) Microsoft. All rights reserved.

import json
from functools import reduce
from unittest.mock import Mock, patch

import boto3
import pytest

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_text_completion import BedrockTextCompletion
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import (
    get_text_completion_request_body,
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from tests.unit.connectors.ai.bedrock.conftest import MockBedrockClient, MockBedrockRuntimeClient

# region init


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_completion_init(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Completion service"""
    bedrock_text_completion = BedrockTextCompletion()

    assert bedrock_text_completion.ai_model_id == bedrock_unit_test_env["BEDROCK_TEXT_MODEL_ID"]
    assert bedrock_text_completion.service_id == bedrock_unit_test_env["BEDROCK_TEXT_MODEL_ID"]

    assert bedrock_text_completion.bedrock_client is not None
    assert bedrock_text_completion.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_completion_init_model_id_override(mock_client, bedrock_unit_test_env, model_id) -> None:
    """Test initialization of Amazon Bedrock Text Completion service"""
    bedrock_text_completion = BedrockTextCompletion(model_id=model_id)

    assert bedrock_text_completion.ai_model_id == model_id
    assert bedrock_text_completion.service_id == model_id

    assert bedrock_text_completion.bedrock_client is not None
    assert bedrock_text_completion.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_completion_init_custom_service_id(mock_client, bedrock_unit_test_env, service_id) -> None:
    """Test initialization of Amazon Bedrock Text Completion service"""
    bedrock_text_completion = BedrockTextCompletion(service_id=service_id)

    assert bedrock_text_completion.service_id == service_id

    assert bedrock_text_completion.bedrock_client is not None
    assert bedrock_text_completion.bedrock_runtime_client is not None


def test_bedrock_text_completion_init_custom_clients(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Completion service"""
    bedrock_text_completion = BedrockTextCompletion(
        runtime_client=MockBedrockRuntimeClient(),
        client=MockBedrockClient(),
    )

    assert isinstance(bedrock_text_completion.bedrock_client, MockBedrockClient)
    assert isinstance(bedrock_text_completion.bedrock_runtime_client, MockBedrockRuntimeClient)


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_completion_init_custom_client(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Completion service"""
    bedrock_text_completion = BedrockTextCompletion(
        client=MockBedrockClient(),
    )

    assert isinstance(bedrock_text_completion.bedrock_client, MockBedrockClient)
    assert bedrock_text_completion.bedrock_runtime_client is not None


@patch.object(boto3, "client", return_value=Mock())
def test_bedrock_text_completion_init_custom_runtime_client(mock_client, bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Completion service"""
    bedrock_text_completion = BedrockTextCompletion(
        runtime_client=MockBedrockRuntimeClient(),
    )

    assert bedrock_text_completion.bedrock_client is not None
    assert isinstance(bedrock_text_completion.bedrock_runtime_client, MockBedrockRuntimeClient)


@pytest.mark.parametrize("exclude_list", [["BEDROCK_TEXT_MODEL_ID"]], indirect=True)
def test_bedrock_text_completion_client_init_with_empty_model_id(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Completion service with empty model id"""
    with pytest.raises(ServiceInitializationError, match="The Amazon Bedrock Text Model ID is missing."):
        BedrockTextCompletion(env_file_path="fake_env_file_path.env")


def test_bedrock_text_completion_client_init_invalid_settings(bedrock_unit_test_env) -> None:
    """Test initialization of Amazon Bedrock Text Completion service with invalid settings"""
    with pytest.raises(
        ServiceInitializationError, match="Failed to initialize the Amazon Bedrock Text Completion Service."
    ):
        BedrockTextCompletion(model_id=123)  # Model ID must be a string


@patch.object(boto3, "client", return_value=Mock())
def test_prompt_execution_settings_class(mock_client, bedrock_unit_test_env) -> None:
    """Test getting prompt execution settings class"""
    bedrock_completion_client = BedrockTextCompletion()
    assert bedrock_completion_client.get_prompt_execution_settings_class() == BedrockTextPromptExecutionSettings


# endregion


# region text completion


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
        "anthropic.claude",
        "cohere.command",
        "ai21.jamba",
        "meta.llama",
        "mistral.ai",
    ],
    indirect=True,
)
async def test_bedrock_text_completion(
    model_id,
    mock_bedrock_text_completion_response,
    output_text,
) -> None:
    """Test Amazon Bedrock Chat Completion complete method"""
    with patch.object(
        MockBedrockRuntimeClient, "invoke_model", return_value=mock_bedrock_text_completion_response
    ) as mock_model_invoke:
        # Setup
        bedrock_text_completion = BedrockTextCompletion(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        # Act
        settings = BedrockTextPromptExecutionSettings()
        response = await bedrock_text_completion.get_text_contents("Hello!", settings=settings)

        # Assert
        mock_model_invoke.assert_called_once_with(
            body=json.dumps(get_text_completion_request_body(model_id, "Hello!", settings)),
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
        )

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], TextContent)
        assert response[0].ai_model_id == model_id
        assert response[0].text == output_text


@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan",
    ],
    indirect=True,
)
async def test_bedrock_streaming_text_completion(
    model_id,
    mock_bedrock_streaming_text_completion_response,
    output_text,
) -> None:
    """Test Amazon Bedrock Chat Completion complete method"""
    with patch.object(
        MockBedrockRuntimeClient,
        "invoke_model_with_response_stream",
        return_value=mock_bedrock_streaming_text_completion_response,
    ) as mock_invoke_model_with_response_stream:
        # Setup
        bedrock_text_completion = BedrockTextCompletion(
            model_id=model_id,
            runtime_client=MockBedrockRuntimeClient(),
            client=MockBedrockClient(),
        )

        # Act
        settings = BedrockTextPromptExecutionSettings()
        chunks: list[StreamingTextContent] = []
        async for streaming_responses in bedrock_text_completion.get_streaming_text_contents(
            "Hello!", settings=settings
        ):
            chunks.extend(streaming_responses)
        response = reduce(lambda p, r: p + r, chunks)

        # Assert
        mock_invoke_model_with_response_stream.assert_called_once_with(
            body=json.dumps(get_text_completion_request_body(model_id, "Hello!", settings)),
            modelId=model_id,
            accept="application/json",
            contentType="application/json",
        )
        assert isinstance(response, StreamingTextContent)
        assert response.ai_model_id == model_id
        assert response.text == output_text
        assert response.choice_index == 0
        assert isinstance(response.inner_content, list)


# endregion
