# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, Callable
from unittest.mock import AsyncMock, create_autospec, patch

import pytest
from pydantic import ValidationError

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatHistoryAgentThread
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
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
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_initialization_invalid_name_throws():
    with pytest.raises(ValidationError):
        _ = ChatCompletionAgent(
            name="Test Agent",
            id="test_id",
            description="Test Description",
            instructions="Test Instructions",
        )


def test_initialization_with_kernel(kernel: Kernel):
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert kernel == agent.kernel
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


def test_initialization_with_kernel_and_service(kernel: Kernel, azure_openai_unit_test_env, openai_unit_test_env):
    kernel.add_service(AzureChatCompletion(service_id="test_azure"))
    agent = ChatCompletionAgent(
        service=OpenAIChatCompletion(),
        kernel=kernel,
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert kernel == agent.kernel
    assert len(kernel.services) == 2
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


def test_initialization_with_plugins_via_constructor(custom_plugin_class):
    agent = ChatCompletionAgent(
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
        plugins=[custom_plugin_class()],
    )

    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"
    assert agent.kernel.plugins is not None
    assert len(agent.kernel.plugins) == 1


def test_initialization_with_service_via_constructor(openai_unit_test_env):
    agent = ChatCompletionAgent(
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
        service=OpenAIChatCompletion(),
    )

    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"
    assert agent.service is not None
    assert agent.kernel.services["test_chat_model_id"] == agent.service


def test_initialize_chat_history_agent_thread_with_id():
    thread = ChatHistoryAgentThread(thread_id="test_thread_id")
    assert thread is not None
    assert thread.id == "test_thread_id"


async def test_get_response(kernel_with_ai_service: tuple[Kernel, ChatCompletionClientBase]):
    kernel, _ = kernel_with_ai_service
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
        instructions="Test Instructions",
    )

    thread = ChatHistoryAgentThread()

    response = await agent.get_response(messages="test", thread=thread)

    assert response.message.content == "Processed Message"
    assert response.thread is not None


async def test_get_response_exception(kernel_with_ai_service: tuple[Kernel, ChatCompletionClientBase]):
    kernel, mock_ai_service_client = kernel_with_ai_service
    mock_ai_service_client.get_chat_message_contents = AsyncMock(return_value=[])
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
        instructions="Test Instructions",
    )

    thread = ChatHistoryAgentThread()

    with pytest.raises(AgentInvokeException):
        await agent.get_response(messages="test", thread=thread)


async def test_invoke(kernel_with_ai_service: tuple[Kernel, ChatCompletionClientBase]):
    kernel, _ = kernel_with_ai_service
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
        instructions="Test Instructions",
    )

    thread = ChatHistoryAgentThread()

    messages = [message async for message in agent.invoke(messages="test", thread=thread)]

    assert len(messages) == 1
    assert messages[0].message.content == "Processed Message"


async def test_invoke_tool_call_not_added(kernel_with_ai_service: tuple[Kernel, ChatCompletionClientBase]):
    kernel, mock_ai_service_client = kernel_with_ai_service
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
    )

    thread = ChatHistoryAgentThread()

    async def mock_get_chat_message_contents(
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        kernel: Kernel,
        arguments: KernelArguments,
    ):
        responses = [
            ChatMessageContent(role=AuthorRole.TOOL, content="Tool Call Result"),
        ]
        chat_history.messages.extend(responses)
        return responses

    mock_ai_service_client.get_chat_message_contents = AsyncMock(side_effect=mock_get_chat_message_contents)

    messages = [message async for message in agent.invoke(messages="test", thread=thread)]

    assert len(messages) == 1
    assert messages[0].message.content == "Tool Call Result"
    assert messages[0].message.role == AuthorRole.TOOL
    assert messages[0].message.name == "TestAgent"

    thread: ChatHistoryAgentThread = messages[-1].thread
    thread_messages = [message async for message in thread.get_messages()]

    assert len(thread_messages) == 2
    assert thread_messages[0].content == "test"
    assert thread_messages[1].content == "Tool Call Result"
    assert thread_messages[1].name == "TestAgent"
    assert thread_messages[1].role == AuthorRole.TOOL


async def test_invoke_no_service_throws(kernel: Kernel):
    agent = ChatCompletionAgent(kernel=kernel, name="TestAgent")

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke(messages="test", thread=None):
            pass


async def test_invoke_stream(kernel_with_ai_service: tuple[Kernel, ChatCompletionClientBase]):
    kernel, _ = kernel_with_ai_service
    agent = ChatCompletionAgent(kernel=kernel, name="TestAgent")

    thread = ChatHistoryAgentThread()

    with patch(
        "semantic_kernel.connectors.ai.chat_completion_client_base.ChatCompletionClientBase.get_streaming_chat_message_contents",
        return_value=AsyncMock(),
    ) as mock:
        mock.return_value.__aiter__.return_value = [
            [ChatMessageContent(role=AuthorRole.USER, content="Initial Message")]
        ]

        async for response in agent.invoke_stream(messages="Initial Message", thread=thread):
            assert response.message.role == AuthorRole.USER
            assert response.message.content == "Initial Message"


async def test_invoke_stream_tool_call_added(
    kernel_with_ai_service: tuple[Kernel, ChatCompletionClientBase],
    mock_streaming_chat_completion_response,
):
    kernel, mock_ai_service_client = kernel_with_ai_service
    agent = ChatCompletionAgent(kernel=kernel, name="TestAgent")

    thread = ChatHistoryAgentThread()

    mock_ai_service_client.get_streaming_chat_message_contents = mock_streaming_chat_completion_response

    async for response in agent.invoke_stream(messages="Initial Message", thread=thread):
        assert response.message.role in [AuthorRole.SYSTEM, AuthorRole.TOOL]
        assert response.message.content in ["Processed Message 1", "Processed Message 2"]


async def test_invoke_stream_no_service_throws(kernel: Kernel):
    agent = ChatCompletionAgent(kernel=kernel, name="TestAgent")

    thread = ChatHistoryAgentThread()

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke_stream(messages="test", thread=thread):
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


async def test_prepare_agent_chat_history_with_formatted_instructions():
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
        result_history = await agent._prepare_agent_chat_history(history, dummy_kernel, dummy_args)
        mock_format_instructions.assert_awaited_once_with(dummy_kernel, dummy_args)
        assert len(result_history.messages) == 2
        system_message = result_history.messages[0]
        assert system_message.role == AuthorRole.SYSTEM
        assert system_message.content == "Formatted instructions for testing"
        assert system_message.name == agent.name
        assert result_history.messages[1] == user_message


async def test_prepare_agent_chat_history_without_formatted_instructions():
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
        result_history = await agent._prepare_agent_chat_history(history, dummy_kernel, dummy_args)
        mock_format_instructions.assert_awaited_once_with(dummy_kernel, dummy_args)
        assert len(result_history.messages) == 1
        assert result_history.messages[0] == user_message
