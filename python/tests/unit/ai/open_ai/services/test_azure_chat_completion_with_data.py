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
from semantic_kernel.connectors.ai.open_ai.models.chat.azure_chat_with_data_settings import (
    AzureAISearchDataSourceParameters,
    AzureChatWithDataSettings,
    DataSourceType,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion_with_data import (
    AzureChatCompletionWithData,
)


def test_azure_chat_completion_with_data_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    # Test successful initialization
    azure_chat_completion_with_data = AzureChatCompletionWithData(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
        data_source_settings=azure_chat_with_data_settings,
    )

    assert azure_chat_completion_with_data.client is not None
    assert isinstance(azure_chat_completion_with_data.client, AsyncAzureOpenAI)
    assert azure_chat_completion_with_data.ai_model_id == deployment_name
    assert isinstance(azure_chat_completion_with_data, ChatCompletionClientBase)
    assert (
        azure_chat_completion_with_data._data_source_settings
        == azure_chat_with_data_settings
    )


def test_azure_chat_completion_with_data_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    with pytest.raises(ValidationError, match="ai_model_id"):
        AzureChatCompletionWithData(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=logger,
            data_source_settings=azure_chat_with_data_settings,
        )


def test_azure_chat_completion_with_data_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    with pytest.raises(AIException, match="api_key"):
        AzureChatCompletionWithData(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
            log=logger,
            data_source_settings=azure_chat_with_data_settings,
        )


def test_azure_chat_completion_with_data_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletionWithData(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            log=logger,
            data_source_settings=azure_chat_with_data_settings,
        )


def test_azure_chat_completion_with_data_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletionWithData(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=logger,
            data_source_settings=azure_chat_with_data_settings,
        )


def test_azure_chat_completion_with_data_init_with_missing_data_source_settings() -> (
    None
):
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(AIException, match="data_source_settings"):
        AzureChatCompletionWithData(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=logger,
            data_source_settings=None,
        )


def test_azure_chat_completion_with_data_init_with_invalid_data_source_settings() -> (
    None
):
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    # params = AzureAISearchDataSourceParameters(
    #     indexName="test_index",
    #     endpoint="https://test-endpoint-search.com",
    #     key="test_key"
    # )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=None
    )

    with pytest.raises(AIException, match="`data_source_parameters`"):
        AzureChatCompletionWithData(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=logger,
            data_source_settings=azure_chat_with_data_settings,
        )


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

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    complete_request_settings = ChatRequestSettings()

    azure_chat_completion = AzureChatCompletionWithData(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_version=api_version,
        api_key=api_key,
        log=logger,
        data_source_settings=azure_chat_with_data_settings,
    )

    await azure_chat_completion.complete_chat_async(
        messages=messages_in, settings=complete_request_settings
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
                    "type": DataSourceType.AZURE_AI_SEARCH.value,
                    "parameters": asdict(params),
                }
            ]
        },
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters_and_function_calling(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    azure_chat_completion = AzureChatCompletionWithData(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
        data_source_settings=azure_chat_with_data_settings,
    )

    functions = [{"name": "test-function", "description": "test-description"}]
    complete_request_settings = ChatRequestSettings(function_call="test-function")

    await azure_chat_completion.complete_chat_with_functions_async(
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
                    "type": DataSourceType.AZURE_AI_SEARCH.value,
                    "parameters": asdict(params),
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

    params = AzureAISearchDataSourceParameters(
        indexName="test_index",
        endpoint="https://test-endpoint-search.com",
        key="test_key",
    )

    azure_chat_with_data_settings = AzureChatWithDataSettings(
        data_source_type=DataSourceType.AZURE_AI_SEARCH, data_source_parameters=params
    )

    azure_chat_completion = AzureChatCompletionWithData(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        log=logger,
        data_source_settings=azure_chat_with_data_settings,
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
                    "type": DataSourceType.AZURE_AI_SEARCH.value,
                    "parameters": asdict(params),
                }
            ]
        },
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
        "data_source_settings": {
            "data_source_type": DataSourceType.AZURE_AI_SEARCH.value,
            "data_source_parameters": {
                "indexName": "test_index",
                "endpoint": "https://test-endpoint-search.com",
                "key": "test_key",
            },
        },
    }

    azure_chat_completion = AzureChatCompletionWithData.from_dict(settings)
    dumped_settings = azure_chat_completion.to_dict()
    assert dumped_settings["ai_model_id"] == settings["deployment_name"]
    assert settings["endpoint"] in str(dumped_settings["base_url"])
    assert settings["deployment_name"] in str(dumped_settings["base_url"])
    assert settings["api_key"] == dumped_settings["api_key"]
    assert settings["data_source_settings"] == dumped_settings["data_source_settings"]
