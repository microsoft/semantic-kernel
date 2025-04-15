# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent, AzureAIAgentThread
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException


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


async def test_azure_ai_agent_add_chat_message(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.create_message",
    ):
        await agent.add_chat_message("threadId", ChatMessageContent(role="user", content="text"))  # pass anything


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


def test_azure_ai_agent_get_channel_keys(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    keys = list(agent.get_channel_keys())
    assert len(keys) >= 3


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


def test_create_client():
    conn_str = "endpoint;subscription_id;resource_group;project_name"
    credential = MagicMock(spec=DefaultAzureCredential)

    with patch("azure.ai.projects.aio.AIProjectClient.from_connection_string") as mock_from_conn_str:
        mock_client = MagicMock(spec=AIProjectClient)
        mock_from_conn_str.return_value = mock_client

        client = AzureAIAgent.create_client(
            credential=credential,
            conn_str=conn_str,
            extra_arg="extra_value",
        )

        mock_from_conn_str.assert_called_once()
        _, actual_kwargs = mock_from_conn_str.call_args

        assert actual_kwargs["credential"] is credential
        assert actual_kwargs["conn_str"] == conn_str
        assert actual_kwargs["extra_arg"] == "extra_value"
        assert actual_kwargs["user_agent"] is not None
        assert client is mock_client
