# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent, AzureAIAgentThread
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException


async def test_azure_ai_agent_init(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"


async def test_azure_ai_agent_init_with_plugins_via_constructor(
    ai_project_client, ai_agent_definition, custom_plugin_class
):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition, plugins=[custom_plugin_class()])
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"
    assert agent.kernel.plugins is not None
    assert len(agent.kernel.plugins) == 1


async def test_azure_ai_agent_get_response(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    thread = AsyncMock(spec=AzureAIAgentThread)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        response = await agent.get_response(messages="message", thread=thread)
        assert response.message.role == AuthorRole.ASSISTANT
        assert response.message.content == "content"
        assert response.thread is not None


async def test_azure_ai_agent_get_response_exception(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)

    async def fake_invoke(*args, **kwargs):
        yield False, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with (
        patch(
            "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
            side_effect=fake_invoke,
        ),
        pytest.raises(AgentInvokeException),
    ):
        await agent.get_response(messages="message", thread=thread)


async def test_azure_ai_agent_invoke(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke(messages="message", thread=thread):
            results.append(item)

    assert len(results) == 1


async def test_azure_ai_agent_invoke_yields_visible_assistant_message(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    results = []

    assistant_msg = ChatMessageContent(role=AuthorRole.ASSISTANT, content="assistant says hi")

    async def fake_invoke(*args, **kwargs):
        yield True, assistant_msg

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke(messages="message", thread=thread):
            results.append(item)

    assert len(results) == 1
    assert results[0].message is assistant_msg


async def test_azure_ai_agent_invoke_emits_tool_message_via_callback_only(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)

    callback_results = []

    async def handle_callback(msg: ChatMessageContent) -> None:
        callback_results.append(msg)

    tool_msg = ChatMessageContent(role=AuthorRole.ASSISTANT, content="tool call")
    tool_msg.items = [FunctionCallContent(name="tool", arguments="{}")]

    async def fake_invoke(*args, **kwargs):
        yield False, tool_msg

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for _ in agent.invoke(messages="message", thread=thread, on_intermediate_message=handle_callback):
            pass

    assert callback_results == [tool_msg]


async def test_azure_ai_agent_invoke_suppresses_tool_message_without_callback(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)

    tool_msg = ChatMessageContent(role=AuthorRole.ASSISTANT, content="tool call")
    tool_msg.items = [FunctionCallContent(name="tool", arguments="{}")]

    async def fake_invoke(*args, **kwargs):
        yield False, tool_msg  # Not visible, no callback

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        results = [item async for item in agent.invoke(messages="message", thread=thread)]

    assert results == []  # Tool message should be suppressed


async def test_azure_ai_agent_invoke_stream(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream(messages="message", thread=thread):
            results.append(item)

    assert len(results) == 1


async def test_azure_ai_agent_invoke_stream_with_on_new_message_callback(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    thread.id = "test_thread_id"
    results = []

    final_chat_history = ChatHistory()

    async def handle_stream_completion(message: ChatMessageContent) -> None:
        final_chat_history.add_message(message)

    # Fake collected messages
    fake_message = StreamingChatMessageContent(role=AuthorRole.ASSISTANT, content="fake content", choice_index=0)

    async def fake_invoke(*args, output_messages=None, **kwargs):
        if output_messages is not None:
            output_messages.append(fake_message)
        yield fake_message

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream(
            messages="message", thread=thread, on_intermediate_message=handle_stream_completion
        ):
            results.append(item)

    assert len(results) == 1
    assert results[0].message.content == "fake content"
    assert len(final_chat_history.messages) == 1
    assert final_chat_history.messages[0].content == "fake content"


async def test_azure_ai_agent_invoke_stream_tool_message_only_goes_to_callback(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    thread.id = "test_thread_id"

    received_callback_messages = []

    async def async_append(msg: ChatMessageContent):
        received_callback_messages.append(msg)

    tool_msg = ChatMessageContent(
        role=AuthorRole.ASSISTANT, content="tool call", items=[FunctionCallContent(name="ToolA", arguments="{}")]
    )

    streamed_msg = StreamingChatMessageContent(
        role=AuthorRole.ASSISTANT, content="assistant streaming...", choice_index=0
    )

    async def fake_invoke_stream(*args, output_messages=None, **kwargs):
        if output_messages is not None:
            output_messages.append(tool_msg)
        yield streamed_msg

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke_stream,
    ):
        results = []
        async for item in agent.invoke_stream(messages="message", thread=thread, on_intermediate_message=async_append):
            results.append(item)

    assert results == [AgentResponseItem(message=streamed_msg, thread=thread)]

    assert received_callback_messages == [tool_msg]


async def test_azure_ai_agent_invoke_stream_tool_message_suppressed_without_callback(
    ai_project_client, ai_agent_definition
):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    thread.id = "test_thread_id"

    tool_msg = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        content="tool result",
        items=[FunctionResultContent(id="test-id", name="ToolA", result="result")],
    )

    streamed_msg = StreamingChatMessageContent(role=AuthorRole.ASSISTANT, content="assistant says hi", choice_index=0)

    async def fake_invoke_stream(*args, output_messages=None, **kwargs):
        if output_messages is not None:
            output_messages.append(tool_msg)
        yield streamed_msg

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke_stream,
    ):
        results = []
        async for item in agent.invoke_stream(messages="message", thread=thread):
            results.append(item)

    # Only assistant-visible content should be yielded
    assert len(results) == 1
    assert results[0].message == streamed_msg


async def test_azure_ai_agent_invoke_stream_mixed_messages(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    thread = AsyncMock(spec=AzureAIAgentThread)
    thread.id = "test_thread_id"

    callback_results = []

    async def async_append(msg: ChatMessageContent):
        callback_results.append(msg)

    tool_msg = ChatMessageContent(
        role=AuthorRole.ASSISTANT, content="tool call", items=[FunctionCallContent(name="tool", arguments="{}")]
    )

    text_msg = StreamingChatMessageContent(role=AuthorRole.ASSISTANT, content="streamed text", choice_index=0)

    async def fake_invoke_stream(*args, output_messages: list = None, **kwargs):
        if output_messages is not None:
            output_messages.append(tool_msg)
        yield text_msg

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke_stream,
    ):
        results = []
        async for item in agent.invoke_stream(messages="message", thread=thread, on_intermediate_message=async_append):
            results.append(item)

    assert callback_results == [tool_msg]
    assert results == [AgentResponseItem(message=text_msg, thread=thread)]


def test_azure_ai_agent_get_channel_keys(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    keys = list(agent.get_channel_keys())
    assert len(keys) >= 2


async def test_azure_ai_agent_create_channel(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    with (
        patch(
            "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.create_thread",
            side_effect="t",
        ),
        patch(
            "semantic_kernel.agents.azure_ai.azure_ai_agent.AzureAIAgentThread.create",
            new_callable=AsyncMock,
        ),
        patch(
            "semantic_kernel.agents.azure_ai.azure_ai_agent.AzureAIAgentThread.id",
            new_callable=PropertyMock,
        ) as mock_id,
    ):
        mock_id.return_value = "mock-thread-id"

        ch = await agent.create_channel()

        assert isinstance(ch, AgentChannel)
        assert ch.thread_id == "mock-thread-id"


def test_create_client_with_explicit_endpoint():
    credential = MagicMock(spec=DefaultAzureCredential)

    with patch("semantic_kernel.agents.azure_ai.azure_ai_agent.AIProjectClient") as mock_client_cls:
        mock_client = MagicMock(spec=AIProjectClient)
        mock_client_cls.return_value = mock_client

        result = AzureAIAgent.create_client(
            credential=credential,
            endpoint="https://my-endpoint",
            extra_arg="extra_value",
        )

        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args

        assert kwargs["credential"] is credential
        assert kwargs["endpoint"] == "https://my-endpoint"
        assert kwargs["extra_arg"] == "extra_value"
        assert result is mock_client


def test_create_client_uses_settings_when_endpoint_none():
    credential = MagicMock(spec=DefaultAzureCredential)

    with (
        patch("semantic_kernel.agents.azure_ai.azure_ai_agent.AzureAIAgentSettings") as mock_settings_cls,
        patch("semantic_kernel.agents.azure_ai.azure_ai_agent.AIProjectClient") as mock_client_cls,
    ):
        mock_settings = MagicMock()
        mock_settings.endpoint = "https://configured-endpoint"
        mock_settings_cls.return_value = mock_settings

        mock_client = MagicMock(spec=AIProjectClient)
        mock_client_cls.return_value = mock_client

        result = AzureAIAgent.create_client(credential=credential)

        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args

        assert kwargs["endpoint"] == "https://configured-endpoint"
        assert result is mock_client


def test_create_client_raises_if_no_endpoint():
    credential = MagicMock(spec=DefaultAzureCredential)

    with patch("semantic_kernel.agents.azure_ai.azure_ai_agent.AzureAIAgentSettings") as mock_settings_cls:
        mock_settings = MagicMock()
        mock_settings.endpoint = None
        mock_settings_cls.return_value = mock_settings

        try:
            AzureAIAgent.create_client(credential=credential)
        except AgentInitializationException as e:
            assert "Azure AI endpoint" in str(e)
        else:
            assert False, "Expected AgentInitializationException to be raised"
