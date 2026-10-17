# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic import AsyncAnthropic
from anthropic.types import Message

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import AnthropicChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent, FunctionCallContent, TextContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceResponseException,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


async def test_complete_chat_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_chat_message_response: Message,
):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(return_value=mock_chat_message_response)
    client.messages = messages_mock

    chat_history = ChatHistory()
    chat_history.add_user_message("test_user_message")

    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    content: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
    )

    assert len(content) > 0
    assert content[0].content != ""
    assert content[0].role == AuthorRole.ASSISTANT


mock_message_text_content = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[TextContent(text="test")])

mock_message_function_call = ChatMessageContent(
    role=AuthorRole.ASSISTANT,
    items=[
        FunctionCallContent(
            name="test",
            arguments={"key": "test"},
        )
    ],
)


@pytest.mark.parametrize(
    "function_choice_behavior,model_responses,expected_result",
    [
        pytest.param(
            FunctionChoiceBehavior.Auto(),
            [[mock_message_function_call], [mock_message_text_content]],
            TextContent,
            id="auto",
        ),
        pytest.param(
            FunctionChoiceBehavior.Auto(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="auto_none_invoke",
        ),
        pytest.param(
            FunctionChoiceBehavior.Required(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="required_none_invoke",
        ),
    ],
)
async def test_complete_chat_contents_function_call_behavior_tool_call(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    function_choice_behavior: FunctionChoiceBehavior,
    model_responses,
    expected_result,
):
    kernel.add_function("test", kernel_function(lambda key: "test", name="test"))
    mock_settings.function_choice_behavior = function_choice_behavior

    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(ai_model_id="test_model_id", service_id="test", api_key="")

    with (
        patch.object(chat_completion_base, "_inner_get_chat_message_contents", side_effect=model_responses),
    ):
        response: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
            chat_history=ChatHistory(system_message="Test"), settings=mock_settings, kernel=kernel, arguments=arguments
        )

        assert all(isinstance(content, expected_result) for content in response[0].items)


async def test_complete_chat_contents_function_call_behavior_without_kernel(
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_anthropic_client_completion: AsyncAnthropic,
):
    chat_history = MagicMock()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    mock_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await chat_completion_base.get_chat_message_contents(chat_history=chat_history, settings=mock_settings)


async def test_complete_chat_stream_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_streaming_message_response,
):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.return_value = mock_streaming_message_response
    client.messages = messages_mock

    chat_history = ChatHistory()
    chat_history.add_user_message("test_user_message")

    arguments = KernelArguments()

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=client,
    )

    async for content in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, mock_settings, kernel=kernel, arguments=arguments
    ):
        assert content is not None


mock_message_function_call = StreamingChatMessageContent(
    role=AuthorRole.ASSISTANT, items=[FunctionCallContent(name="test")], choice_index="0"
)

mock_message_text_content = StreamingChatMessageContent(
    role=AuthorRole.ASSISTANT, items=[TextContent(text="test")], choice_index="0"
)


@pytest.mark.parametrize(
    "function_choice_behavior,model_responses,expected_result",
    [
        pytest.param(
            FunctionChoiceBehavior.Auto(),
            [[mock_message_function_call], [mock_message_text_content]],
            TextContent,
            id="auto",
        ),
        pytest.param(
            FunctionChoiceBehavior.Auto(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="auto_none_invoke",
        ),
        pytest.param(
            FunctionChoiceBehavior.Required(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="required_none_invoke",
        ),
        pytest.param(FunctionChoiceBehavior.NoneInvoke(), [[mock_message_text_content]], TextContent, id="none"),
    ],
)
async def test_complete_chat_contents_streaming_function_call_behavior_tool_call(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    function_choice_behavior: FunctionChoiceBehavior,
    model_responses,
    expected_result,
):
    mock_settings.function_choice_behavior = function_choice_behavior

    # Mock sequence of model responses
    generator_mocks = []
    for mock_message in model_responses:
        generator_mock = MagicMock()
        generator_mock.__aiter__.return_value = [mock_message]
        generator_mocks.append(generator_mock)

    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(ai_model_id="test_model_id", service_id="test", api_key="")

    with patch.object(chat_completion_base, "_inner_get_streaming_chat_message_contents", side_effect=generator_mocks):
        messages = []
        async for chunk in chat_completion_base.get_streaming_chat_message_contents(
            chat_history=ChatHistory(system_message="Test"), settings=mock_settings, kernel=kernel, arguments=arguments
        ):
            messages.append(chunk)

        response = messages[-1]
        assert all(isinstance(content, expected_result) for content in response[0].items)


async def test_anthropic_sdk_exception(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.create.side_effect = Exception("Test Exception")
    client.messages = messages_mock

    chat_history = MagicMock()
    arguments = KernelArguments()

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        await chat_completion_base.get_chat_message_contents(
            chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
        )


async def test_anthropic_sdk_exception_streaming(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.side_effect = Exception("Test Exception")
    client.messages = messages_mock

    chat_history = MagicMock()
    arguments = KernelArguments()

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        async for content in chat_completion_base.get_streaming_chat_message_contents(
            chat_history, mock_settings, kernel=kernel, arguments=arguments
        ):
            assert content is not None


def test_anthropic_chat_completion_init(anthropic_unit_test_env) -> None:
    # Test successful initialization
    anthropic_chat_completion = AnthropicChatCompletion()

    assert anthropic_chat_completion.ai_model_id == anthropic_unit_test_env["ANTHROPIC_CHAT_MODEL_ID"]
    assert isinstance(anthropic_chat_completion, ChatCompletionClientBase)


@pytest.mark.parametrize("exclude_list", [["ANTHROPIC_API_KEY"]], indirect=True)
def test_anthropic_chat_completion_init_with_empty_api_key(anthropic_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        AnthropicChatCompletion(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["ANTHROPIC_CHAT_MODEL_ID"]], indirect=True)
def test_anthropic_chat_completion_init_with_empty_model_id(anthropic_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AnthropicChatCompletion(
            env_file_path="test.env",
        )


def test_prompt_execution_settings_class(anthropic_unit_test_env):
    anthropic_chat_completion = AnthropicChatCompletion()
    prompt_execution_settings = anthropic_chat_completion.get_prompt_execution_settings_class()
    assert prompt_execution_settings == AnthropicChatPromptExecutionSettings


async def test_with_different_execution_settings(kernel: Kernel, mock_anthropic_client_completion: MagicMock):
    chat_history = MagicMock()
    settings = OpenAIChatPromptExecutionSettings(temperature=0.2)
    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=settings, kernel=kernel, arguments=arguments
    )

    assert mock_anthropic_client_completion.messages.create.call_args.kwargs["temperature"] == 0.2


async def test_with_different_execution_settings_stream(
    kernel: Kernel, mock_anthropic_client_completion_stream: MagicMock
):
    chat_history = MagicMock()
    settings = OpenAIChatPromptExecutionSettings(temperature=0.2, seed=2)
    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    async for chunk in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    ):
        assert chunk is not None
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2


async def test_prepare_chat_history_for_request_with_system_message(mock_anthropic_client_completion_stream: MagicMock):
    chat_history = ChatHistory()
    chat_history.add_system_message("System message")
    chat_history.add_user_message("User message")
    chat_history.add_assistant_message("Assistant message")
    chat_history.add_system_message("Another system message")

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    remaining_messages, system_message_content = chat_completion_base._prepare_chat_history_for_request(
        chat_history, role_key="role", content_key="content"
    )

    assert system_message_content == "System message"
    assert remaining_messages == [
        {"role": AuthorRole.USER, "content": "User message"},
        {"role": AuthorRole.ASSISTANT, "content": [{"type": "text", "text": "Assistant message"}]},
    ]
    assert not any(msg["role"] == AuthorRole.SYSTEM for msg in remaining_messages)


async def test_prepare_chat_history_for_request_with_tool_message(
    mock_anthropic_client_completion_stream: MagicMock,
    mock_tool_calls_message: ChatMessageContent,
    mock_tool_call_result_message: ChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_tool_calls_message)
    chat_history.add_message(mock_tool_call_result_message)

    chat_completion_client = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    remaining_messages, system_message_content = chat_completion_client._prepare_chat_history_for_request(
        chat_history, role_key="role", content_key="content"
    )

    assert system_message_content is None
    assert remaining_messages == [
        {"role": AuthorRole.USER, "content": "What is 3+3?"},
        {
            "role": AuthorRole.ASSISTANT,
            "content": [
                {"type": "text", "text": mock_tool_calls_message.items[0].text},
                {
                    "type": "tool_use",
                    "id": mock_tool_calls_message.items[1].id,
                    "name": mock_tool_calls_message.items[1].name,
                    "input": mock_tool_calls_message.items[1].arguments,
                },
            ],
        },
        {
            "role": AuthorRole.USER,
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": mock_tool_call_result_message.items[0].id,
                    "content": str(mock_tool_call_result_message.items[0].result),
                }
            ],
        },
    ]


async def test_prepare_chat_history_for_request_with_parallel_tool_message(
    mock_anthropic_client_completion_stream: MagicMock,
    mock_parallel_tool_calls_message: ChatMessageContent,
    mock_parallel_tool_call_result_message: ChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_parallel_tool_calls_message)
    chat_history.add_message(mock_parallel_tool_call_result_message)

    chat_completion_client = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    remaining_messages, system_message_content = chat_completion_client._prepare_chat_history_for_request(
        chat_history, role_key="role", content_key="content"
    )

    assert system_message_content is None
    assert remaining_messages == [
        {"role": AuthorRole.USER, "content": "What is 3+3?"},
        {
            "role": AuthorRole.ASSISTANT,
            "content": [
                {"type": "text", "text": mock_parallel_tool_calls_message.items[0].text},
                *[
                    {
                        "type": "tool_use",
                        "id": function_call_content.id,
                        "name": function_call_content.name,
                        "input": function_call_content.arguments,
                    }
                    for function_call_content in mock_parallel_tool_calls_message.items[1:]
                ],
            ],
        },
        {
            "role": AuthorRole.USER,
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": function_result_content.id,
                    "content": str(function_result_content.result),
                }
                for function_result_content in mock_parallel_tool_call_result_message.items
            ],
        },
    ]


async def test_prepare_chat_history_for_request_with_tool_message_right_after_user_message(
    mock_anthropic_client_completion_stream: MagicMock,
    mock_tool_call_result_message: ChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_tool_call_result_message)

    chat_completion_client = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    with pytest.raises(ServiceInvalidRequestError, match="Tool message found after a user or system message."):
        chat_completion_client._prepare_chat_history_for_request(chat_history, role_key="role", content_key="content")


async def test_prepare_chat_history_for_request_with_tool_message_as_the_first_message(
    mock_anthropic_client_completion_stream: MagicMock,
    mock_tool_call_result_message: ChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_message(mock_tool_call_result_message)

    chat_completion_client = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    with pytest.raises(ServiceInvalidRequestError, match="Tool message found without a preceding message."):
        chat_completion_client._prepare_chat_history_for_request(chat_history, role_key="role", content_key="content")


async def test_send_chat_stream_request_tool_calls(
    mock_streaming_tool_calls_message: MagicMock,
    mock_streaming_chat_message_content: StreamingChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_streaming_chat_message_content)

    settings = AnthropicChatPromptExecutionSettings(
        temperature=0.2,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        chat_history=chat_history,
    )

    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.return_value = mock_streaming_tool_calls_message
    client.messages = messages_mock

    chat_completion = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=client,
    )

    response = chat_completion._send_chat_stream_request(settings)
    async for message in response:
        assert message is not None


def test_client_base_url(mock_anthropic_client_completion: MagicMock):
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    assert chat_completion_base.service_url() is not None


def test_chat_completion_reset_settings(
    mock_anthropic_client_completion: MagicMock,
):
    chat_completion = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    settings = AnthropicChatPromptExecutionSettings(tools=[{"name": "test"}], tool_choice={"type": "any"})
    chat_completion._reset_function_choice_settings(settings)

    assert settings.tools is None
    assert settings.tool_choice is None


def test_default_headers_with_app_info(anthropic_unit_test_env) -> None:
    app_info = {"semantic-kernel-version": "python/1.0.0"}
    mock_client = MagicMock(spec=AsyncAnthropic)
    with (
        patch(
            "semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion.APP_INFO",
            app_info,
        ),
        patch(
            "semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion.AsyncAnthropic",
            return_value=mock_client,
        ) as mock_async_anthropic,
    ):
        AnthropicChatCompletion()

        mock_async_anthropic.assert_called_once()
        call_kwargs = mock_async_anthropic.call_args.kwargs
        headers = call_kwargs["default_headers"]
        assert "semantic-kernel-version" in headers
        assert headers["semantic-kernel-version"] == "python/1.0.0"
        assert "User-Agent" in headers


def test_default_headers_merged_with_custom_headers(anthropic_unit_test_env) -> None:
    app_info = {"semantic-kernel-version": "python/1.0.0"}
    custom_headers = {"X-Custom-Header": "custom-value"}
    mock_client = MagicMock(spec=AsyncAnthropic)
    with (
        patch(
            "semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion.APP_INFO",
            app_info,
        ),
        patch(
            "semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion.AsyncAnthropic",
            return_value=mock_client,
        ) as mock_async_anthropic,
    ):
        AnthropicChatCompletion(default_headers=custom_headers)

        call_kwargs = mock_async_anthropic.call_args.kwargs
        headers = call_kwargs["default_headers"]
        assert headers["X-Custom-Header"] == "custom-value"
        assert headers["semantic-kernel-version"] == "python/1.0.0"
        assert "User-Agent" in headers


def test_default_headers_without_app_info(anthropic_unit_test_env) -> None:
    mock_client = MagicMock(spec=AsyncAnthropic)
    with (
        patch(
            "semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion.APP_INFO",
            None,
        ),
        patch(
            "semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion.AsyncAnthropic",
            return_value=mock_client,
        ) as mock_async_anthropic,
    ):
        AnthropicChatCompletion()

        call_kwargs = mock_async_anthropic.call_args.kwargs
        headers = call_kwargs["default_headers"]
        assert headers == {}
