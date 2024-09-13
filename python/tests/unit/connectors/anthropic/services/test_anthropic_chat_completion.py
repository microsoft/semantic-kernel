# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock

import pytest
from anthropic import AsyncAnthropic
from anthropic.lib.streaming import TextEvent
from anthropic.types import (
    ContentBlockStopEvent,
    Message,
    MessageDeltaUsage,
    MessageStopEvent,
    RawContentBlockDeltaEvent,
    RawContentBlockStartEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
    TextDelta,
    Usage,
)
from anthropic.types.raw_message_delta_event import Delta

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import AnthropicChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
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
    chat_completion_response.content = [TextBlock(text="Hello! It's nice to meet you.", type="text")]
    chat_completion_response.id = "test_id"
    chat_completion_response.model = "claude-3-opus-20240229"
    chat_completion_response.role = "assistant"
    chat_completion_response.stop_reason = "end_turn"
    chat_completion_response.stop_sequence = None
    chat_completion_response.type = "message"
    chat_completion_response.usage = Usage(input_tokens=114, output_tokens=75)

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(return_value=chat_completion_response)

    # Assign the messages_mock to the client.messages attribute
    client.messages = messages_mock

    return client


@pytest.fixture
def mock_anthropic_client_completion_stream() -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)

    # Create MagicMock instances for each event with the spec set to the appropriate class
    mock_raw_message_start_event = MagicMock(spec=RawMessageStartEvent)
    mock_raw_message_start_event.message = MagicMock(spec=Message)
    mock_raw_message_start_event.message.id = "test_message_id"
    mock_raw_message_start_event.message.content = []
    mock_raw_message_start_event.message.model = "claude-3-opus-20240229"
    mock_raw_message_start_event.message.role = "assistant"
    mock_raw_message_start_event.message.stop_reason = None
    mock_raw_message_start_event.message.stop_sequence = None
    mock_raw_message_start_event.message.type = "message"
    mock_raw_message_start_event.message.usage = MagicMock(spec=Usage)
    mock_raw_message_start_event.message.usage.input_tokens = 41
    mock_raw_message_start_event.message.usage.output_tokens = 3
    mock_raw_message_start_event.type = "message_start"

    mock_raw_content_block_start_event = MagicMock(spec=RawContentBlockStartEvent)
    mock_raw_content_block_start_event.content_block = MagicMock(spec=TextBlock)
    mock_raw_content_block_start_event.content_block.text = ""
    mock_raw_content_block_start_event.content_block.type = "text"
    mock_raw_content_block_start_event.index = 0
    mock_raw_content_block_start_event.type = "content_block_start"

    mock_raw_content_block_delta_event = MagicMock(spec=RawContentBlockDeltaEvent)
    mock_raw_content_block_delta_event.delta = MagicMock(spec=TextDelta)
    mock_raw_content_block_delta_event.delta.text = "Hello! It"
    mock_raw_content_block_delta_event.delta.type = "text_delta"
    mock_raw_content_block_delta_event.index = 0
    mock_raw_content_block_delta_event.type = "content_block_delta"

    mock_text_event = MagicMock(spec=TextEvent)
    mock_text_event.type = "text"
    mock_text_event.text = "Hello! It"
    mock_text_event.snapshot = "Hello! It"

    mock_content_block_stop_event = MagicMock(spec=ContentBlockStopEvent)
    mock_content_block_stop_event.index = 0
    mock_content_block_stop_event.type = "content_block_stop"
    mock_content_block_stop_event.content_block = MagicMock(spec=TextBlock)
    mock_content_block_stop_event.content_block.text = "Hello! It's nice to meet you."
    mock_content_block_stop_event.content_block.type = "text"

    mock_raw_message_delta_event = MagicMock(spec=RawMessageDeltaEvent)
    mock_raw_message_delta_event.delta = MagicMock(spec=Delta)
    mock_raw_message_delta_event.delta.stop_reason = "end_turn"
    mock_raw_message_delta_event.delta.stop_sequence = None
    mock_raw_message_delta_event.type = "message_delta"
    mock_raw_message_delta_event.usage = MagicMock(spec=MessageDeltaUsage)
    mock_raw_message_delta_event.usage.output_tokens = 84

    mock_message_stop_event = MagicMock(spec=MessageStopEvent)
    mock_message_stop_event.type = "message_stop"
    mock_message_stop_event.message = MagicMock(spec=Message)
    mock_message_stop_event.message.id = "test_message_stop_id"
    mock_message_stop_event.message.content = [MagicMock(spec=TextBlock)]
    mock_message_stop_event.message.content[0].text = "Hello! It's nice to meet you."
    mock_message_stop_event.message.content[0].type = "text"
    mock_message_stop_event.message.model = "claude-3-opus-20240229"
    mock_message_stop_event.message.role = "assistant"
    mock_message_stop_event.message.stop_reason = "end_turn"
    mock_message_stop_event.message.stop_sequence = None
    mock_message_stop_event.message.type = "message"
    mock_message_stop_event.message.usage = MagicMock(spec=Usage)
    mock_message_stop_event.message.usage.input_tokens = 41
    mock_message_stop_event.message.usage.output_tokens = 84

    # Combine all mock events into a list
    stream_events = [
        mock_raw_message_start_event,
        mock_raw_content_block_start_event,
        mock_raw_content_block_delta_event,
        mock_text_event,
        mock_content_block_stop_event,
        mock_raw_message_delta_event,
        mock_message_stop_event,
    ]

    async def async_generator():
        for event in stream_events:
            yield event

    # Create an AsyncMock for the stream
    stream_mock = AsyncMock()
    stream_mock.__aenter__.return_value = async_generator()

    messages_mock = MagicMock()
    messages_mock.stream.return_value = stream_mock

    client.messages = messages_mock

    return client


@pytest.mark.asyncio
async def test_complete_chat_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_anthropic_client_completion: AsyncAnthropic,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("test_user_message")
    chat_history.add_assistant_message("test_assistant_message")

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


@pytest.mark.asyncio
async def test_prepare_chat_history_for_request_with_system_message(
    kernel: Kernel, mock_anthropic_client_completion_stream: MagicMock
):
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
        {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
    ]

    assert not any(msg["role"] == AuthorRole.SYSTEM for msg in remaining_messages)
