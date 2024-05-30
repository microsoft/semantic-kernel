# Copyright (c) Microsoft. All rights reserved.

import os
from unittest.mock import AsyncMock, patch

import openai
import pytest
from httpx import Request, Response
from openai import AsyncAzureOpenAI
from openai.resources.chat.completions import AsyncCompletions as AsyncChatCompletions

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.const import USER_AGENT
from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import (
    ContentFilterAIException,
    ContentFilterResultSeverity,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureAISearchDataSource,
    AzureChatPromptExecutionSettings,
    ExtraBody,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidExecutionSettingsError
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.kernel import Kernel


def test_azure_chat_completion_init(azure_openai_unit_test_env) -> None:
    # Test successful initialization
    azure_chat_completion = AzureChatCompletion()

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)


def test_azure_chat_completion_init_base_url(azure_openai_unit_test_env) -> None:
    # Custom header for testing
    default_headers = {"X-Unit-Test": "test-guid"}

    azure_chat_completion = AzureChatCompletion(
        default_headers=default_headers,
    )

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)
    for key, value in default_headers.items():
        assert key in azure_chat_completion.client.default_headers
        assert azure_chat_completion.client.default_headers[key] == value


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_chat_completion_init_with_empty_deployment_name(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion()


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_chat_completion_init_with_empty_api_key(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion()


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_azure_chat_completion_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion()


@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
def test_azure_chat_completion_init_with_invalid_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion()


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters(
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    chat_history.add_user_message("hello world")
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(service_id="test_service_id")

    azure_chat_completion = AzureChatCompletion()
    await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
    )
    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        stream=False,
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters_and_Logit_Bias_Defined(
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "hello world"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    token_bias = {"1": -100}
    complete_prompt_execution_settings.logit_bias = token_bias

    azure_chat_completion = AzureChatCompletion()

    await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
    )

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        stream=False,
        logit_bias=token_bias,
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_parameters_and_Stop_Defined(
    mock_create,
    azure_openai_unit_test_env,
) -> None:
    prompt = "hello world"
    messages = [{"role": "user", "content": prompt}]
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    stop = ["!"]
    complete_prompt_execution_settings.stop = stop

    azure_chat_completion = AzureChatCompletion()

    await azure_chat_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=messages,
        stream=False,
        stop=complete_prompt_execution_settings.stop,
    )


def test_azure_chat_completion_serialize(azure_openai_unit_test_env) -> None:
    default_headers = {"X-Test": "test"}

    settings = {
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        "endpoint": azure_openai_unit_test_env["AZURE_OPENAI_ENDPOINT"],
        "api_key": azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"],
        "api_version": azure_openai_unit_test_env["AZURE_OPENAI_API_VERSION"],
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
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "hello world"
    messages_in = chat_history
    messages_in.add_user_message(prompt)
    messages_out = ChatHistory()
    messages_out.add_user_message(prompt)

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

    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(extra_body=expected_data_settings)

    azure_chat_completion = AzureChatCompletion()

    await azure_chat_completion.get_chat_message_contents(
        chat_history=messages_in, settings=complete_prompt_execution_settings, kernel=kernel
    )

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(messages_out),
        stream=False,
        extra_body=expected_data_settings,
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_data_parameters_and_function_calling(
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "hello world"
    chat_history.add_user_message(prompt)

    ai_source = AzureAISearchDataSource(
        parameters={
            "indexName": "test-index",
            "endpoint": "test-endpoint",
            "authentication": {"type": "api_key", "api_key": "test-key"},
        }
    )
    extra = ExtraBody(data_sources=[ai_source])

    azure_chat_completion = AzureChatCompletion()

    functions = [{"name": "test-function", "description": "test-description"}]
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_call="test-function",
        functions=functions,
        extra_body=extra,
    )

    await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=complete_prompt_execution_settings,
        kernel=kernel,
    )

    expected_data_settings = extra.model_dump(exclude_none=True, by_alias=True)

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        stream=False,
        extra_body=expected_data_settings,
        functions=functions,
        function_call=complete_prompt_execution_settings.function_call,
    )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_chat_completion_call_with_data_with_parameters_and_Stop_Defined(
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    chat_history.add_user_message("hello world")
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    stop = ["!"]
    complete_prompt_execution_settings.stop = stop

    ai_source = AzureAISearchDataSource(
        parameters={
            "indexName": "test-index",
            "endpoint": "test-endpoint",
            "authentication": {"type": "api_key", "api_key": "test-key"},
        }
    )
    extra = ExtraBody(data_sources=[ai_source])

    complete_prompt_execution_settings.extra_body = extra

    azure_chat_completion = AzureChatCompletion()

    await azure_chat_completion.get_chat_message_contents(
        chat_history, complete_prompt_execution_settings, kernel=kernel
    )

    expected_data_settings = extra.model_dump(exclude_none=True, by_alias=True)

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        stream=False,
        stop=complete_prompt_execution_settings.stop,
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
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "some prompt that would trigger the content filtering"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    test_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    mock_create.side_effect = openai.BadRequestError(
        CONTENT_FILTERED_ERROR_FULL_MESSAGE,
        response=Response(400, request=Request("POST", test_endpoint)),
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

    azure_chat_completion = AzureChatCompletion()

    with pytest.raises(ContentFilterAIException, match="service encountered a content error") as exc_info:
        await azure_chat_completion.get_chat_message_contents(
            chat_history, complete_prompt_execution_settings, kernel=kernel
        )

    content_filter_exc = exc_info.value
    assert content_filter_exc.param == "prompt"
    assert content_filter_exc.content_filter_result["hate"].filtered
    assert content_filter_exc.content_filter_result["hate"].severity == ContentFilterResultSeverity.HIGH


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create")
async def test_azure_chat_completion_content_filtering_without_response_code_raises_with_default_code(
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "some prompt that would trigger the content filtering"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    test_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    mock_create.side_effect = openai.BadRequestError(
        CONTENT_FILTERED_ERROR_FULL_MESSAGE,
        response=Response(400, request=Request("POST", test_endpoint)),
        body={
            "message": CONTENT_FILTERED_ERROR_MESSAGE,
            "type": None,
            "param": "prompt",
            "code": "content_filter",
            "status": 400,
            "innererror": {
                "content_filter_result": {
                    "hate": {"filtered": True, "severity": "high"},
                    "self_harm": {"filtered": False, "severity": "safe"},
                    "sexual": {"filtered": False, "severity": "safe"},
                    "violence": {"filtered": False, "severity": "safe"},
                },
            },
        },
    )

    azure_chat_completion = AzureChatCompletion()

    with pytest.raises(ContentFilterAIException, match="service encountered a content error"):
        await azure_chat_completion.get_chat_message_contents(
            chat_history, complete_prompt_execution_settings, kernel=kernel
        )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create")
async def test_azure_chat_completion_bad_request_non_content_filter(
    mock_create, kernel: Kernel, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "some prompt that would trigger the content filtering"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    test_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    mock_create.side_effect = openai.BadRequestError(
        "The request was bad.", response=Response(400, request=Request("POST", test_endpoint)), body={}
    )

    azure_chat_completion = AzureChatCompletion()

    with pytest.raises(ServiceResponseException, match="service failed to complete the prompt"):
        await azure_chat_completion.get_chat_message_contents(
            chat_history, complete_prompt_execution_settings, kernel=kernel
        )


@pytest.mark.asyncio
@patch.object(AsyncChatCompletions, "create")
async def test_azure_chat_completion_no_kernel_provided_throws_error(
    mock_create, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "some prompt that would trigger the content filtering"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_call_behavior=FunctionCallBehavior.AutoInvokeKernelFunctions()
    )

    test_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    mock_create.side_effect = openai.BadRequestError(
        "The request was bad.", response=Response(400, request=Request("POST", test_endpoint)), body={}
    )

    azure_chat_completion = AzureChatCompletion()

    with pytest.raises(
        ServiceInvalidExecutionSettingsError,
        match="The kernel and kernel arguments are required for auto invoking OpenAI tool calls.",
    ):
        await azure_chat_completion.get_chat_message_contents(chat_history, complete_prompt_execution_settings)
