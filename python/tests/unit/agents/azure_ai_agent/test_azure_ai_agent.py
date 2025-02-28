# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

import pytest
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
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

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        response = await agent.get_response("thread_id")
        assert response.role == AuthorRole.ASSISTANT
        assert response.content == "content"


async def test_azure_ai_agent_get_response_exception(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    async def fake_invoke(*args, **kwargs):
        yield False, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with (
        patch(
            "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
            side_effect=fake_invoke,
        ),
        pytest.raises(AgentInvokeException),
    ):
        await agent.get_response("thread_id")


async def test_azure_ai_agent_invoke(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke("thread_id"):
            results.append(item)

    assert len(results) == 1


async def test_azure_ai_agent_invoke_stream(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream("thread_id"):
            results.append(item)

    assert len(results) == 1


def test_azure_ai_agent_get_channel_keys(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    keys = list(agent.get_channel_keys())
    assert len(keys) >= 3


async def test_azure_ai_agent_create_channel(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.create_thread",
        side_effect="t",
    ):
        ch = await agent.create_channel()
        assert isinstance(ch, AgentChannel)
        assert ch.thread_id == "t"


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
