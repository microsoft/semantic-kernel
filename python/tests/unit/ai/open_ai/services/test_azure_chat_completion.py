# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import openai
import pytest
from httpx import Request, Response
from openai import AsyncAzureOpenAI
from openai.resources.chat.completions import AsyncCompletions as AsyncChatCompletions
from pydantic import ValidationError

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.const import (
    USER_AGENT,
)
from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import (
    ContentFilterAIException,
    ContentFilterCodes,
    ContentFilterResultSeverity,
)
from semantic_kernel.connectors.ai.open_ai.request_settings.azure_chat_request_settings import (
    AzureAISearchDataSources,
    AzureChatRequestSettings,
    AzureDataSources,
    ExtraBody,
)


def test_azure_chat_completion_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    # Test successful initialization
    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == deployment_name
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)


def test_azure_chat_completion_init_base_url() -> None:
    deployment_name = "test_deployment"
    base_url = "https://test-endpoint.com/openai/deployment/test_deployment"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    # Custom header for testing
    default_headers = {"X-Unit-Test": "test-guid"}

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        base_url=base_url,
        api_key=api_key,
        api_version=api_version,
        default_headers=default_headers,
    )

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == deployment_name
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)
    for key, value in default_headers.items():
        assert key in azure_chat_completion.client.default_headers
        assert azure_chat_completion.client.default_headers[key] == value


def test_azure_chat_completion_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="ai_model_id"):
        AzureChatCompletion(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_chat_completion_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(AIException, match="api_key"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
        )


def test_azure_chat_completion_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_chat_completion_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_chat_completion_init_with_base_url() -> None:
    deployment_name = "test_deployment"
    base_url = "http://test-endpoint.com/openai/deployment/test_deployment"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="url"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            base_url=base_url,
            api_key=api_key,
            api_version=api_version,
        )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters(mock_create) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    messages = [{"role": "user", "content": "hello world"}]
    complete_request_settings = AzureChatRequestSettings(service_id="test_service_id")

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_version=api_version,
        api_key=api_key,
    )
    await azure_chat_completion.complete_chat_async(messages=messages, settings=complete_request_settings)
    mock_create.assert_awaited_once_with(
        model=deployment_name,
        frequency_penalty=complete_request_settings.frequency_penalty,
        logit_bias={},
        max_tokens=complete_request_settings.max_tokens,
        n=complete_request_settings.number_of_responses,
        presence_penalty=complete_request_settings.presence_penalty,
        stream=False,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        messages=messages,
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

    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]
    complete_request_settings = AzureChatRequestSettings()

    token_bias = {"1": -100}
    complete_request_settings.logit_bias = token_bias

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_chat_completion.complete_chat_async(messages=messages, settings=complete_request_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
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

    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]
    complete_request_settings = AzureChatRequestSettings()

    stop = ["!"]
    complete_request_settings.stop = stop

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_chat_completion.complete_async(prompt, complete_request_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        stop=complete_request_settings.stop,
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
    default_headers = {"X-Test": "test"}

    settings = {
        "deployment_name": deployment_name,
        "endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "default_headers": default_headers,
    }

    azure_chat_completion = AzureChatCompletion.from_dict(settings)
    dumped_settings = azure_chat_completion.to_dict()
    assert dumped_settings["ai_model_id"] == settings["deployment_name"]
    assert settings["endpoint"] in str(dumped_settings["base_url"])
    assert settings["deployment_name"] in str(dumped_settings["base_url"])
    assert settings["api_key"] == dumped_settings["api_key"]
    assert settings["api_version"] == dumped_settings["api_version"]

    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value

    # Assert that the 'User-agent' header is not present in the dumped_settings default headers
    assert USER_AGENT not in dumped_settings["default_headers"]


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_with_data_call_with_parameters(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    prompt = "hello world"
    messages_in = [{"role": "user", "content": prompt}]
    messages_out = [{"role": "user", "content": prompt}]

    expected_data_settings = {
        "dataSources": [
            {
                "type": "AzureCognitiveSearch",
                "parameters": {
                    "indexName": "test_index",
                    "endpoint": "https://test-endpoint-search.com",
                    "key": "test_key",
                },
            }
        ]
    }

    complete_request_settings = AzureChatRequestSettings(extra_body=expected_data_settings)

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_version=api_version,
        api_key=api_key,
    )

    await azure_chat_completion.complete_chat_async(messages=messages_in, settings=complete_request_settings)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages_out,
        temperature=complete_request_settings.temperature,
        frequency_penalty=complete_request_settings.frequency_penalty,
        presence_penalty=complete_request_settings.presence_penalty,
        logit_bias={},
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        max_tokens=complete_request_settings.max_tokens,
        extra_body=expected_data_settings,
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
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]

    ai_source = AzureAISearchDataSources(indexName="test-index", endpoint="test-endpoint", key="test-key")
    extra = ExtraBody(data_sources=[AzureDataSources(type="AzureCognitiveSearch", parameters=ai_source)])

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    functions = [{"name": "test-function", "description": "test-description"}]
    complete_request_settings = AzureChatRequestSettings(
        function_call="test-function",
        functions=functions,
        extra_body=extra,
    )

    await azure_chat_completion.complete_chat_async(
        messages=messages,
        settings=complete_request_settings,
    )

    expected_data_settings = extra.model_dump(exclude_none=True, by_alias=True)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        max_tokens=complete_request_settings.max_tokens,
        presence_penalty=complete_request_settings.presence_penalty,
        frequency_penalty=complete_request_settings.frequency_penalty,
        logit_bias=complete_request_settings.logit_bias,
        extra_body=expected_data_settings,
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
    messages = [{"role": "user", "content": "hello world"}]
    complete_request_settings = AzureChatRequestSettings()

    stop = ["!"]
    complete_request_settings.stop = stop

    ai_source = AzureAISearchDataSources(indexName="test-index", endpoint="test-endpoint", key="test-key")
    extra = ExtraBody(data_sources=[AzureDataSources(type="AzureCognitiveSearch", parameters=ai_source)])

    complete_request_settings.extra_body = extra

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_chat_completion.complete_chat_async(messages, complete_request_settings)

    expected_data_settings = extra.model_dump(exclude_none=True, by_alias=True)

    mock_create.assert_awaited_once_with(
        model=deployment_name,
        messages=messages,
        temperature=complete_request_settings.temperature,
        top_p=complete_request_settings.top_p,
        n=complete_request_settings.number_of_responses,
        stream=False,
        stop=complete_request_settings.stop,
        max_tokens=complete_request_settings.max_tokens,
        presence_penalty=complete_request_settings.presence_penalty,
        frequency_penalty=complete_request_settings.frequency_penalty,
        logit_bias={},
        extra_body=expected_data_settings,
    )


CONTENT_FILTERED_ERROR_MESSAGE = (
    "The response was filtered due to the prompt triggering Azure OpenAI's content management policy. Please "
    "modify your prompt and retry. To learn more about our content filtering policies please read our "
    "documentation: https://go.microsoft.com/fwlink/?linkid=2198766"
)
CONTENT_FILTERED_ERROR_FULL_MESSAGE = (
    "Error code: 400 - {'error': {'message': \"%s\", 'type': null, 'param': 'prompt', 'code': 'content_filter', "
    "'status': 400, 'innererror': {'code': 'ResponsibleAIPolicyViolation', 'content_filter_result': {'hate': "
    "{'filtered': True, 'severity': 'high'}, 'self_harm': {'filtered': False, 'severity': 'safe'}, 'sexual': "
    "{'filtered': False, 'severity': 'safe'}, 'violence': {'filtered': False, 'severity': 'safe'}}}}}"
) % CONTENT_FILTERED_ERROR_MESSAGE


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create")
async def test_azure_chat_completion_content_filtering_raises_correct_exception(
    mock_create,
) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    prompt = "some prompt that would trigger the content filtering"
    messages = [{"role": "user", "content": prompt}]
    complete_request_settings = AzureChatRequestSettings()

    mock_create.side_effect = openai.BadRequestError(
        CONTENT_FILTERED_ERROR_FULL_MESSAGE,
        response=Response(400, request=Request("POST", endpoint)),
        body={
            "message": CONTENT_FILTERED_ERROR_MESSAGE,
            "type": None,
            "param": "prompt",
            "code": "content_filter",
            "status": 400,
            "innererror": {
                "code": "ResponsibleAIPolicyViolation",
                "content_filter_result": {
                    "hate": {"filtered": True, "severity": "high"},
                    "self_harm": {"filtered": False, "severity": "safe"},
                    "sexual": {"filtered": False, "severity": "safe"},
                    "violence": {"filtered": False, "severity": "safe"},
                },
            },
        },
    )

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    with pytest.raises(ContentFilterAIException, match="service encountered a content error") as exc_info:
        await azure_chat_completion.complete_chat_async(messages, complete_request_settings)

    content_filter_exc = exc_info.value
    assert content_filter_exc.param == "prompt"
    assert content_filter_exc.content_filter_code == ContentFilterCodes.RESPONSIBLE_AI_POLICY_VIOLATION
    assert content_filter_exc.content_filter_result["hate"].filtered
    assert content_filter_exc.content_filter_result["hate"].severity == ContentFilterResultSeverity.HIGH
