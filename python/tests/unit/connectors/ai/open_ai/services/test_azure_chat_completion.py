# Copyright (c) Microsoft. All rights reserved.

import json
import os
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest
from httpx import Request, Response
from openai import AsyncAzureOpenAI, AsyncStream
from openai.resources.chat.completions import AsyncCompletions as AsyncChatCompletions
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta as ChunkChoiceDelta
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import (
    ContentFilterAIException,
    ContentFilterResultSeverity,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.const import USER_AGENT
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidExecutionSettingsError
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

# region Service Setup


def test_init(azure_openai_unit_test_env) -> None:
    # Test successful initialization
    azure_chat_completion = AzureChatCompletion(service_id="test_service_id")

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)
    assert azure_chat_completion.get_prompt_execution_settings_class() == AzureChatPromptExecutionSettings


def test_init_client(azure_openai_unit_test_env) -> None:
    # Test successful initialization with client
    client = MagicMock(spec=AsyncAzureOpenAI)
    azure_chat_completion = AzureChatCompletion(async_client=client)

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)


def test_init_base_url(azure_openai_unit_test_env) -> None:
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


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_init_endpoint(azure_openai_unit_test_env) -> None:
    azure_chat_completion = AzureChatCompletion()

    assert azure_chat_completion.client is not None
    assert isinstance(azure_chat_completion.client, AsyncAzureOpenAI)
    assert azure_chat_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]
    assert isinstance(azure_chat_completion, ChatCompletionClientBase)


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
def test_init_with_empty_deployment_name(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
def test_init_with_invalid_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureChatCompletion()


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_serialize(azure_openai_unit_test_env) -> None:
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


# endregion
# region CMC


@pytest.fixture
def mock_chat_completion_response() -> ChatCompletion:
    return ChatCompletion(
        id="test_id",
        choices=[
            Choice(index=0, message=ChatCompletionMessage(content="test", role="assistant"), finish_reason="stop")
        ],
        created=0,
        model="test",
        object="chat.completion",
    )


@pytest.fixture
def mock_streaming_chat_completion_response() -> AsyncStream[ChatCompletionChunk]:
    content = ChatCompletionChunk(
        id="test_id",
        choices=[ChunkChoice(index=0, delta=ChunkChoiceDelta(content="test", role="assistant"), finish_reason="stop")],
        created=0,
        model="test",
        object="chat.completion.chunk",
    )
    stream = MagicMock(spec=AsyncStream)
    stream.__aiter__.return_value = [content]
    return stream


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_create.return_value = mock_chat_completion_response
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


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_with_developer_instruction_role_propagates(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_create.return_value = mock_chat_completion_response
    chat_history.add_user_message("hello world")
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(service_id="test_service_id")

    azure_chat_completion = AzureChatCompletion(instruction_role="developer")
    await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
    )
    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        stream=False,
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
    )
    assert azure_chat_completion.instruction_role == "developer"


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_with_logit_bias(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_create.return_value = mock_chat_completion_response
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


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_with_stop(
    mock_create,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_create.return_value = mock_chat_completion_response
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    stop = ["!"]
    complete_prompt_execution_settings.stop = stop

    azure_chat_completion = AzureChatCompletion()

    await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history, settings=complete_prompt_execution_settings
    )

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        stream=False,
        stop=stop,
    )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_on_your_data(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content="test",
                role="assistant",
                context={
                    "citations": {
                        "content": "test content",
                        "title": "test title",
                        "url": "test url",
                        "filepath": "test filepath",
                        "chunk_id": "test chunk_id",
                    },
                    "intent": "query used",
                },
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    messages_in = chat_history
    messages_in.add_user_message(prompt)
    messages_out = ChatHistory()
    messages_out.add_user_message(prompt)

    expected_data_settings = {
        "data_sources": [
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

    content = await azure_chat_completion.get_chat_message_contents(
        chat_history=messages_in, settings=complete_prompt_execution_settings, kernel=kernel
    )
    assert isinstance(content[0].items[0], FunctionCallContent)
    assert isinstance(content[0].items[1], FunctionResultContent)
    assert isinstance(content[0].items[2], TextContent)
    assert content[0].items[2].text == "test"

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(messages_out),
        stream=False,
        extra_body=expected_data_settings,
    )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_on_your_data_string(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content="test",
                role="assistant",
                context=json.dumps({
                    "citations": {
                        "content": "test content",
                        "title": "test title",
                        "url": "test url",
                        "filepath": "test filepath",
                        "chunk_id": "test chunk_id",
                    },
                    "intent": "query used",
                }),
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    messages_in = chat_history
    messages_in.add_user_message(prompt)
    messages_out = ChatHistory()
    messages_out.add_user_message(prompt)

    expected_data_settings = {
        "data_sources": [
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

    content = await azure_chat_completion.get_chat_message_contents(
        chat_history=messages_in, settings=complete_prompt_execution_settings, kernel=kernel
    )
    assert isinstance(content[0].items[0], FunctionCallContent)
    assert isinstance(content[0].items[1], FunctionResultContent)
    assert isinstance(content[0].items[2], TextContent)
    assert content[0].items[2].text == "test"

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(messages_out),
        stream=False,
        extra_body=expected_data_settings,
    )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_on_your_data_fail(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content="test",
                role="assistant",
                context="not a dictionary",
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    messages_in = chat_history
    messages_in.add_user_message(prompt)
    messages_out = ChatHistory()
    messages_out.add_user_message(prompt)

    expected_data_settings = {
        "data_sources": [
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

    content = await azure_chat_completion.get_chat_message_contents(
        chat_history=messages_in, settings=complete_prompt_execution_settings, kernel=kernel
    )
    assert isinstance(content[0].items[0], TextContent)
    assert content[0].items[0].text == "test"

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(messages_out),
        stream=False,
        extra_body=expected_data_settings,
    )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_azure_on_your_data_split_messages(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content="test",
                role="assistant",
                context={
                    "citations": {
                        "content": "test content",
                        "title": "test title",
                        "url": "test url",
                        "filepath": "test filepath",
                        "chunk_id": "test chunk_id",
                    },
                    "intent": "query used",
                },
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    messages_in = chat_history
    messages_in.add_user_message(prompt)
    messages_out = ChatHistory()
    messages_out.add_user_message(prompt)

    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    azure_chat_completion = AzureChatCompletion()

    content = await azure_chat_completion.get_chat_message_contents(
        chat_history=messages_in, settings=complete_prompt_execution_settings, kernel=kernel
    )
    messages = azure_chat_completion.split_message(content[0])
    assert len(messages) == 3
    assert isinstance(messages[0].items[0], FunctionCallContent)
    assert isinstance(messages[1].items[0], FunctionResultContent)
    assert isinstance(messages[2].items[0], TextContent)
    assert messages[2].items[0].text == "test"
    message = azure_chat_completion.split_message(messages[0])
    assert message == [messages[0]]


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_function_calling(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content=None,
                role="assistant",
                function_call={"name": "test-function", "arguments": '{"key": "value"}'},
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    chat_history.add_user_message(prompt)

    azure_chat_completion = AzureChatCompletion()

    functions = [{"name": "test-function", "description": "test-description"}]
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_call="test-function",
        functions=functions,
    )

    content = await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=complete_prompt_execution_settings,
        kernel=kernel,
    )
    assert isinstance(content[0].items[0], FunctionCallContent)

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        stream=False,
        functions=functions,
        function_call=complete_prompt_execution_settings.function_call,
    )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_tool_calling(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content=None,
                role="assistant",
                tool_calls=[
                    {
                        "id": "test id",
                        "function": {"name": "test-tool", "arguments": '{"key": "value"}'},
                        "type": "function",
                    }
                ],
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    chat_history.add_user_message(prompt)

    azure_chat_completion = AzureChatCompletion()

    complete_prompt_execution_settings = AzureChatPromptExecutionSettings()

    content = await azure_chat_completion.get_chat_message_contents(
        chat_history=chat_history,
        settings=complete_prompt_execution_settings,
        kernel=kernel,
    )
    assert isinstance(content[0].items[0], FunctionCallContent)
    assert content[0].items[0].id == "test id"

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        stream=False,
    )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_tool_calling_parallel_tool_calls(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content=None,
                role="assistant",
                tool_calls=[
                    {
                        "id": "test id",
                        "function": {"name": "test-tool", "arguments": '{"key": "value"}'},
                        "type": "function",
                    }
                ],
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    chat_history.add_user_message(prompt)

    class MockPlugin:
        @kernel_function(name="test_tool")
        def test_tool(self, key: str):
            return "test"

    kernel.add_plugin(MockPlugin(), plugin_name="test_tool")

    orig_chat_history = deepcopy(chat_history)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        service_id="test_service_id", function_choice_behavior=FunctionChoiceBehavior.Auto()
    )

    with patch(
        "semantic_kernel.kernel.Kernel.invoke_function_call",
        new_callable=AsyncMock,
    ) as mock_process_function_call:
        azure_chat_completion = AzureChatCompletion()
        await azure_chat_completion.get_chat_message_contents(
            chat_history=chat_history,
            settings=complete_prompt_execution_settings,
            kernel=kernel,
            arguments=KernelArguments(),
        )
        mock_create.assert_awaited_once_with(
            model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            stream=False,
            messages=azure_chat_completion._prepare_chat_history_for_request(orig_chat_history),
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "test_tool-test_tool",
                        "description": "",
                        "parameters": {
                            "type": "object",
                            "properties": {"key": {"type": "string"}},
                            "required": ["key"],
                        },
                    },
                }
            ],
            tool_choice="auto",
        )
        mock_process_function_call.assert_awaited()


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_tool_calling_parallel_tool_calls_disabled(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_chat_completion_response: ChatCompletion,
) -> None:
    mock_chat_completion_response.choices = [
        Choice(
            index=0,
            message=ChatCompletionMessage(
                content=None,
                role="assistant",
                tool_calls=[
                    {
                        "id": "test id",
                        "function": {"name": "test-tool", "arguments": '{"key": "value"}'},
                        "type": "function",
                    }
                ],
            ),
            finish_reason="stop",
        )
    ]
    mock_create.return_value = mock_chat_completion_response
    prompt = "hello world"
    chat_history.add_user_message(prompt)

    class MockPlugin:
        @kernel_function(name="test_tool")
        def test_tool(self, key: str):
            return "test"

    kernel.add_plugin(MockPlugin(), plugin_name="test_tool")

    orig_chat_history = deepcopy(chat_history)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        service_id="test_service_id",
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
        parallel_tool_calls=False,
    )

    with patch(
        "semantic_kernel.kernel.Kernel.invoke_function_call",
        new_callable=AsyncMock,
    ) as mock_process_function_call:
        azure_chat_completion = AzureChatCompletion()
        await azure_chat_completion.get_chat_message_contents(
            chat_history=chat_history,
            settings=complete_prompt_execution_settings,
            kernel=kernel,
            arguments=KernelArguments(),
        )
        mock_create.assert_awaited_once_with(
            model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            stream=False,
            messages=azure_chat_completion._prepare_chat_history_for_request(orig_chat_history),
            parallel_tool_calls=False,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "test_tool-test_tool",
                        "description": "",
                        "parameters": {
                            "type": "object",
                            "properties": {"key": {"type": "string"}},
                            "required": ["key"],
                        },
                    },
                }
            ],
            tool_choice="auto",
        )
        mock_process_function_call.assert_awaited()


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


@patch.object(AsyncChatCompletions, "create")
async def test_content_filtering_raises_correct_exception(
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
            chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
        )

    content_filter_exc = exc_info.value
    assert content_filter_exc.param == "prompt"
    assert content_filter_exc.content_filter_result["hate"].filtered
    assert content_filter_exc.content_filter_result["hate"].severity == ContentFilterResultSeverity.HIGH


@patch.object(AsyncChatCompletions, "create")
async def test_content_filtering_without_response_code_raises_with_default_code(
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
            chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
        )


@patch.object(AsyncChatCompletions, "create")
async def test_bad_request_non_content_filter(
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
            chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
        )


@patch.object(AsyncChatCompletions, "create")
async def test_no_kernel_provided_throws_error(
    mock_create, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "some prompt that would trigger the content filtering"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )

    test_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    mock_create.side_effect = openai.BadRequestError(
        "The request was bad.", response=Response(400, request=Request("POST", test_endpoint)), body={}
    )

    azure_chat_completion = AzureChatCompletion()

    with pytest.raises(
        ServiceInvalidExecutionSettingsError,
        match="The kernel is required for function calls.",
    ):
        await azure_chat_completion.get_chat_message_contents(
            chat_history=chat_history, settings=complete_prompt_execution_settings
        )


@patch.object(AsyncChatCompletions, "create")
async def test_auto_invoke_false_no_kernel_provided_throws_error(
    mock_create, azure_openai_unit_test_env, chat_history: ChatHistory
) -> None:
    prompt = "some prompt that would trigger the content filtering"
    chat_history.add_user_message(prompt)
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=False)
    )

    test_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    mock_create.side_effect = openai.BadRequestError(
        "The request was bad.", response=Response(400, request=Request("POST", test_endpoint)), body={}
    )

    azure_chat_completion = AzureChatCompletion()

    with pytest.raises(
        ServiceInvalidExecutionSettingsError,
        match="The kernel is required for function calls.",
    ):
        await azure_chat_completion.get_chat_message_contents(
            chat_history=chat_history, settings=complete_prompt_execution_settings
        )


@patch.object(AsyncChatCompletions, "create", new_callable=AsyncMock)
async def test_cmc_streaming(
    mock_create,
    kernel: Kernel,
    azure_openai_unit_test_env,
    chat_history: ChatHistory,
    mock_streaming_chat_completion_response: AsyncStream[ChatCompletionChunk],
) -> None:
    mock_create.return_value = mock_streaming_chat_completion_response
    chat_history.add_user_message("hello world")
    complete_prompt_execution_settings = AzureChatPromptExecutionSettings(service_id="test_service_id")

    azure_chat_completion = AzureChatCompletion()
    async for msg in azure_chat_completion.get_streaming_chat_message_contents(
        chat_history=chat_history, settings=complete_prompt_execution_settings, kernel=kernel
    ):
        assert msg is not None
    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        stream=True,
        messages=azure_chat_completion._prepare_chat_history_for_request(chat_history),
        # NOTE: The `stream_options={"include_usage": True}` is explicitly enforced in
        # `OpenAIChatCompletionBase._inner_get_streaming_chat_message_contents`.
        # To ensure consistency, we align the arguments here accordingly.
        stream_options={"include_usage": True},
    )
