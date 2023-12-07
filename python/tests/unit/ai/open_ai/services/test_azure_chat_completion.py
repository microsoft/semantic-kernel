# Copyright (c) Microsoft. All rights reserved.

from dataclasses import asdict
from logging import Logger
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.chat.completions import AsyncCompletions as AsyncChatCompletions
from pydantic import ValidationError

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.semantic_functions.prompt_template_with_data_config import (
    PromptTemplateWithDataConfig,
)


def test_azure_chat_completion_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    # Test successful initialization
    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
    )

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == deployment_name
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)


def test_azure_chat_completion_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="ai_model_id"):
        AzureChatCompletion(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=logger,
        )


def test_azure_chat_completion_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(AIException, match="api_key"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
            log=logger,
        )


def test_azure_chat_completion_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            log=logger,
        )


def test_azure_chat_completion_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=logger,
        )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters(mock_create) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages_in = [{"role": "user", "content": prompt}]
    messages_out = [{"role": "user", "content": prompt}]
    complete_request_settings = ChatRequestSettings()

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_version=api_version,
        api_key=api_key,
        log=logger,
    )
    await azure_chat_completion.complete_chat_async(
        messages=messages_in, settings=complete_request_settings
    )
    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages_out,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        stop=None,
        max_tokens=complete_request_settings.max_tokens,
        presence_penalty=complete_request_settings.presence_penalty,
        frequency_penalty=complete_request_settings.frequency_penalty,
        logit_bias={},
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters_and_Logit_Bias_Defined(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]
    complete_request_settings = ChatRequestSettings()

    token_bias = {1: -100}
    complete_request_settings.token_selection_biases = token_bias

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
    )

    await azure_chat_completion.complete_chat_async(
        messages=messages, settings=complete_request_settings
    )

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        stop=None,
        max_tokens=complete_request_settings.max_tokens,
        presence_penalty=complete_request_settings.presence_penalty,
        frequency_penalty=complete_request_settings.frequency_penalty,
        logit_bias=token_bias,
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters_and_Stop_Defined(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]
    complete_request_settings = ChatRequestSettings()

    stop = ["!"]
    complete_request_settings.stop_sequences = stop

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
    )

    await azure_chat_completion.complete_async(prompt, complete_request_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        stop=complete_request_settings.stop_sequences,
        max_tokens=complete_request_settings.max_tokens,
        presence_penalty=complete_request_settings.presence_penalty,
        frequency_penalty=complete_request_settings.frequency_penalty,
        logit_bias={},
    )


def test_azure_chat_completion_serialize() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    settings = {
        "deployment_name": deployment_name,
        "endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "log": logger,
    }

    azure_chat_completion = AzureChatCompletion.from_dict(settings)
    dumped_settings = azure_chat_completion.to_dict()
    assert dumped_settings["ai_model_id"] == settings["deployment_name"]
    assert settings["endpoint"] in str(dumped_settings["base_url"])
    assert settings["deployment_name"] in str(dumped_settings["base_url"])
    assert settings["api_key"] == dumped_settings["api_key"]


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_with_data_call_with_parameters(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages_in = [{"role": "user", "content": prompt}]
    messages_out = [{"role": "user", "content": prompt}]

    azure_chat_with_data_settings = PromptTemplateWithDataConfig.AzureChatWithDataSettings(
        data_source_parameters=PromptTemplateWithDataConfig.AzureAISearchDataSourceParameters(
            indexName="test_index",
            endpoint="https://test-endpoint-search.com",
            key="test_key",
        )
    )
    complete_request_settings = ChatRequestSettings(
        data_source_settings=azure_chat_with_data_settings
    )

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_version=api_version,
        api_key=api_key,
        log=logger,
    )

    await azure_chat_completion.complete_chat_with_data_async(
        messages=messages_in, request_settings=complete_request_settings
    )

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages_out,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        # n=complete_request_settings.number_of_responses,
        stream=False,
        stop=None,
        max_tokens=complete_request_settings.max_tokens,
        # presence_penalty=complete_request_settings.presence_penalty,
        # frequency_penalty=complete_request_settings.frequency_penalty,
        # logit_bias={},
        extra_body={
            "dataSources": [
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": asdict(
                        azure_chat_with_data_settings.data_source_parameters
                    ),
                }
            ]
        },
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_data_parameters_and_function_calling(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]

    azure_chat_with_data_settings = PromptTemplateWithDataConfig.AzureChatWithDataSettings(
        data_source_parameters=PromptTemplateWithDataConfig.AzureAISearchDataSourceParameters(
            indexName="test_index",
            endpoint="https://test-endpoint-search.com",
            key="test_key",
        )
    )

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
    )

    functions = [{"name": "test-function", "description": "test-description"}]
    complete_request_settings = ChatRequestSettings(
        function_call="test-function",
        data_source_settings=azure_chat_with_data_settings,
    )

    await azure_chat_completion.complete_chat_with_data_async(
        messages=messages,
        functions=functions,
        request_settings=complete_request_settings,
    )

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        # n=complete_request_settings.number_of_responses,
        stream=False,
        stop=None,
        max_tokens=complete_request_settings.max_tokens,
        # presence_penalty=complete_request_settings.presence_penalty,
        # frequency_penalty=complete_request_settings.frequency_penalty,
        # logit_bias=token_bias,
        extra_body={
            "dataSources": [
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": asdict(
                        azure_chat_with_data_settings.data_source_parameters
                    ),
                }
            ]
        },
        functions=functions,
        function_call=complete_request_settings.function_call,
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_data_with_parameters_and_Stop_Defined(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]
    complete_request_settings = ChatRequestSettings()

    stop = ["!"]
    complete_request_settings.stop_sequences = stop

    azure_chat_with_data_settings = PromptTemplateWithDataConfig.AzureChatWithDataSettings(
        data_source_parameters=PromptTemplateWithDataConfig.AzureAISearchDataSourceParameters(
            indexName="test_index",
            endpoint="https://test-endpoint-search.com",
            key="test_key",
        )
    )
    complete_request_settings.data_source_settings = azure_chat_with_data_settings

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
    )

    await azure_chat_completion.complete_chat_async(messages, complete_request_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        # n=complete_request_settings.number_of_responses,
        stream=False,
        stop=complete_request_settings.stop_sequences,
        max_tokens=complete_request_settings.max_tokens,
        # presence_penalty=complete_request_settings.presence_penalty,
        # frequency_penalty=complete_request_settings.frequency_penalty,
        # logit_bias={},
        extra_body={
            "dataSources": [
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": asdict(
                        azure_chat_with_data_settings.data_source_parameters
                    ),
                }
            ]
        },
    )
