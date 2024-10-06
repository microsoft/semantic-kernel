# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.completions import AsyncCompletions
from pydantic import ValidationError

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)


def test_azure_text_completion_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    # Test successful initialization
    azure_text_completion = AzureTextCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    assert azure_text_completion.client is not None
    assert isinstance(azure_text_completion.client, AsyncAzureOpenAI)
    assert azure_text_completion.ai_model_id == deployment_name
    assert isinstance(azure_text_completion, TextCompletionClientBase)


def test_azure_text_completion_init_with_custom_header() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    # Custom header for testing
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    azure_text_completion = AzureTextCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        default_headers=default_headers,
    )

    assert azure_text_completion.client is not None
    assert isinstance(azure_text_completion.client, AsyncAzureOpenAI)
    assert azure_text_completion.ai_model_id == deployment_name
    assert isinstance(azure_text_completion, TextCompletionClientBase)
    for key, value in default_headers.items():
        assert key in azure_text_completion.client.default_headers
        assert azure_text_completion.client.default_headers[key] == value


def test_azure_text_completion_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="ai_model_id"):
        AzureTextCompletion(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_text_completion_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(AIException, match="api_key"):
        AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
        )


def test_azure_text_completion_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="endpoint"):
        AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_text_completion_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="https"):
        AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_azure_text_completion_call_with_parameters(mock_create) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    prompt = "hello world"
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings()
    azure_text_completion = AzureTextCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_text_completion.complete(prompt, complete_prompt_execution_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        frequency_penalty=complete_prompt_execution_settings.frequency_penalty,
        logit_bias={},
        max_tokens=complete_prompt_execution_settings.max_tokens,
        n=complete_prompt_execution_settings.number_of_responses,
        presence_penalty=complete_prompt_execution_settings.presence_penalty,
        stream=False,
        temperature=complete_prompt_execution_settings.temperature,
        top_p=complete_prompt_execution_settings.top_p,
        prompt=prompt,
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_azure_text_completion_call_with_parameters_logit_bias_not_none(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    prompt = "hello world"
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings()

    token_bias = {"200": 100}
    complete_prompt_execution_settings.logit_bias = token_bias

    azure_text_completion = AzureTextCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_text_completion.complete(prompt, complete_prompt_execution_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        frequency_penalty=complete_prompt_execution_settings.frequency_penalty,
        logit_bias=complete_prompt_execution_settings.logit_bias,
        max_tokens=complete_prompt_execution_settings.max_tokens,
        n=complete_prompt_execution_settings.number_of_responses,
        presence_penalty=complete_prompt_execution_settings.presence_penalty,
        stream=False,
        temperature=complete_prompt_execution_settings.temperature,
        top_p=complete_prompt_execution_settings.top_p,
        prompt=prompt,
        echo=False,
    )


def test_azure_text_completion_serialize() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    default_headers = {"X-Test": "test"}

    settings = {
        "deployment_name": deployment_name,
        "endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "default_headers": default_headers,
    }

    azure_text_completion = AzureTextCompletion.from_dict(settings)
    dumped_settings = azure_text_completion.to_dict()
    assert dumped_settings["ai_model_id"] == settings["deployment_name"]
    assert settings["endpoint"] in str(dumped_settings["base_url"])
    assert settings["deployment_name"] in str(dumped_settings["base_url"])
    assert settings["api_key"] == dumped_settings["api_key"]
    assert settings["api_version"] == dumped_settings["api_version"]

    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value
