# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, Callable
from unittest.mock import AsyncMock, create_autospec, patch

import pytest
from pydantic import ValidationError

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel


@pytest.fixture
def mock_streaming_chat_completion_response() -> Callable[..., AsyncGenerator[list[ChatMessageContent], None]]:
    async def mock_response(
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        kernel: Kernel,
        arguments: KernelArguments,
    ) -> AsyncGenerator[list[ChatMessageContent], None]:
        content1 = ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message 1")
        content2 = ChatMessageContent(role=AuthorRole.TOOL, content="Processed Message 2")
        chat_history.messages.append(content1)
        chat_history.messages.append(content2)
        yield [content1]
        yield [content2]

    return mock_response


async def test_initialization():
    agent = ChatCompletionAgent(
        service_id="test_service",
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "test_service"
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_initialization_invalid_name_throws():
    with pytest.raises(ValidationError):
        _ = ChatCompletionAgent(
            service_id="test_service",
            name="Test Agent",
            id="test_id",
            description="Test Description",
            instructions="Test Instructions",
        )


async def test_initialization_no_service_id():
    agent = ChatCompletionAgent(
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "default"
    assert agent.kernel is not None
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_initialization_with_kernel(kernel: Kernel):
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "default"
    assert kernel == agent.kernel
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_invoke():
    kernel = create_autospec(Kernel)
    mock_ai_service_client = create_autospec(ChatCompletionClientBase)
    mock_prompt_execution_settings = create_autospec(PromptExecutionSettings)
    kernel.select_ai_service.return_value = (mock_ai_service_client, mock_prompt_execution_settings)
    mock_ai_service_client.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )
    agent = ChatCompletionAgent(
        kernel=kernel, service_id="test_service", name="TestAgent", instructions="Test Instructions"
    )

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    messages = [message async for message in agent.invoke(history)]

    assert len(messages) == 1
    assert messages[0].content == "Processed Message"


async def test_invoke_tool_call_added():
    kernel = create_autospec(Kernel)
    mock_ai_service_client = create_autospec(ChatCompletionClientBase)
    mock_prompt_execution_settings = create_autospec(PromptExecutionSettings)
    kernel.select_ai_service.return_value = (mock_ai_service_client, mock_prompt_execution_settings)
    mock_ai_service_client.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    async def mock_get_chat_message_contents(
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        kernel: Kernel,
        arguments: KernelArguments,
    ):
        new_messages = [
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Processed Message 1"),
            ChatMessageContent(role=AuthorRole.TOOL, content="Processed Message 2"),
        ]
        chat_history.messages.extend(new_messages)
        return new_messages

    mock_ai_service_client.get_chat_message_contents = AsyncMock(side_effect=mock_get_chat_message_contents)

    messages = [message async for message in agent.invoke(history)]

    assert len(messages) == 2
    assert messages[0].content == "Processed Message 1"
    assert messages[1].content == "Processed Message 2"

    assert len(history.messages) == 3
    assert history.messages[1].content == "Processed Message 1"
    assert history.messages[2].content == "Processed Message 2"
    assert history.messages[1].name == "TestAgent"
    assert history.messages[2].name == "TestAgent"


async def test_invoke_no_service_throws():
    kernel = create_autospec(Kernel)
    kernel.select_ai_service.return_value = None, None
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke(history):
            pass


async def test_invoke_stream():
    kernel = create_autospec(Kernel)
    mock_ai_service_client = create_autospec(ChatCompletionClientBase)
    mock_prompt_execution_settings = create_autospec(PromptExecutionSettings)
    kernel.select_ai_service.return_value = (mock_ai_service_client, mock_prompt_execution_settings)
    mock_ai_service_client.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )

    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with patch(
        "semantic_kernel.connectors.ai.chat_completion_client_base.ChatCompletionClientBase.get_streaming_chat_message_contents",
        return_value=AsyncMock(),
    ) as mock:
        mock.return_value.__aiter__.return_value = [
            [ChatMessageContent(role=AuthorRole.USER, content="Initial Message")]
        ]

        async for message in agent.invoke_stream(history):
            assert message.role == AuthorRole.USER
            assert message.content == "Initial Message"


async def test_invoke_stream_tool_call_added(mock_streaming_chat_completion_response):
    kernel = create_autospec(Kernel)
    mock_ai_service_client = create_autospec(ChatCompletionClientBase)
    mock_prompt_execution_settings = create_autospec(PromptExecutionSettings)
    kernel.select_ai_service.return_value = (mock_ai_service_client, mock_prompt_execution_settings)
    mock_ai_service_client.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    mock_ai_service_client.get_streaming_chat_message_contents = mock_streaming_chat_completion_response

    async for message in agent.invoke_stream(history):
        print(f"Message role: {message.role}, content: {message.content}")
        assert message.role in [AuthorRole.SYSTEM, AuthorRole.TOOL]
        assert message.content in ["Processed Message 1", "Processed Message 2"]

    assert len(history.messages) == 3


async def test_invoke_stream_no_service_throws():
    kernel = create_autospec(Kernel)
    kernel.select_ai_service.return_value = None, None
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke_stream(history):
            pass


def test_get_channel_keys():
    agent = ChatCompletionAgent()
    keys = agent.get_channel_keys()

    for key in keys:
        assert isinstance(key, str)


async def test_create_channel():
    agent = ChatCompletionAgent()
    channel = await agent.create_channel()

    assert isinstance(channel, ChatHistoryChannel)


async def test_setup_agent_chat_history_with_formatted_instructions():
    agent = ChatCompletionAgent(
        name="TestAgent", id="test_id", description="Test Description", instructions="Test Instructions"
    )
    with patch.object(
        ChatCompletionAgent, "format_instructions", new=AsyncMock(return_value="Formatted instructions for testing")
    ) as mock_format_instructions:
        dummy_kernel = create_autospec(Kernel)
        dummy_args = KernelArguments(param="value")
        user_message = ChatMessageContent(role=AuthorRole.USER, content="User message")
        history = ChatHistory(messages=[user_message])
        result_history = await agent._setup_agent_chat_history(history, dummy_kernel, dummy_args)
        mock_format_instructions.assert_awaited_once_with(dummy_kernel, dummy_args)
        assert len(result_history.messages) == 2
        system_message = result_history.messages[0]
        assert system_message.role == AuthorRole.SYSTEM
        assert system_message.content == "Formatted instructions for testing"
        assert system_message.name == agent.name
        assert result_history.messages[1] == user_message


async def test_setup_agent_chat_history_without_formatted_instructions():
    agent = ChatCompletionAgent(
        name="TestAgent", id="test_id", description="Test Description", instructions="Test Instructions"
    )
    with patch.object(
        ChatCompletionAgent, "format_instructions", new=AsyncMock(return_value=None)
    ) as mock_format_instructions:
        dummy_kernel = create_autospec(Kernel)
        dummy_args = KernelArguments(param="value")
        user_message = ChatMessageContent(role=AuthorRole.USER, content="User message")
        history = ChatHistory(messages=[user_message])
        result_history = await agent._setup_agent_chat_history(history, dummy_kernel, dummy_args)
        mock_format_instructions.assert_awaited_once_with(dummy_kernel, dummy_args)
        assert len(result_history.messages) == 1
        assert result_history.messages[0] == user_message
