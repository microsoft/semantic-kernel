# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock

import pytest
from anthropic import AsyncAnthropic

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import AnthropicChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel


@pytest.fixture
def mock_settings() -> AnthropicChatPromptExecutionSettings:
    return AnthropicChatPromptExecutionSettings()


@pytest.fixture
def mock_anthropic_client_completion() -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)
    chat_completion_response = AsyncMock()
    
    content = [MagicMock(finish_reason="stop", message=MagicMock(role="assistant", content="Test"))]
    chat_completion_response.content = content

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.create = chat_completion_response

    # Assign the messages_mock to the client.messages attribute
    client.messages = messages_mock
    return client


@pytest.fixture
def mock_anthropic_client_completion_stream() -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)
    chat_completion_response = MagicMock()

    content = [
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test")),
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test", tool_calls=None)),
    ]
    chat_completion_response.content = content

    chat_completion_response_empty = MagicMock()
    chat_completion_response_empty.content = []

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.stream = chat_completion_response
    
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [chat_completion_response_empty, chat_completion_response]
    
    client.messages = messages_mock
    
    return client


@pytest.mark.asyncio
async def test_complete_chat_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_anthropic_client_completion: AsyncAnthropic,
):
    chat_history = MagicMock()
    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    content: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
    )
    assert content is not None


@pytest.mark.asyncio
async def test_complete_chat_stream_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_anthropic_client_completion_stream: AsyncAnthropic,
):
    chat_history = MagicMock()
    arguments = KernelArguments()

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    async for content in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, mock_settings, kernel=kernel, arguments=arguments
    ):
        assert content is not None


@pytest.mark.asyncio
async def test_anthropic_sdk_exception(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=AsyncAnthropic)

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.create.side_effect = Exception("Test Exception")

    # Assign the messages_mock to the client.messages attribute
    client.messages = messages_mock

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        await chat_completion_base.get_chat_message_contents(
            chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
        )


@pytest.mark.asyncio
async def test_anthropic_sdk_exception_streaming(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=AsyncAnthropic)

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.stream.side_effect = Exception("Test Exception")

    client.messages = messages_mock

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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
        continue
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2
