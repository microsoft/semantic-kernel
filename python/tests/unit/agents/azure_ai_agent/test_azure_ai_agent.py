# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import Agent as AzureAIAgentModel
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


async def test_azure_ai_agent_init():
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAIAgent(client=client, definition=definition)
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"


async def test_azure_ai_agent_init_with_plugins_via_constructor(custom_plugin_class):
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"

    agent = AzureAIAgent(client=client, definition=definition, plugins=[custom_plugin_class()])
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"
    assert agent.plugins is not None
    assert len(agent.plugins) == 1


async def test_azure_ai_agent_add_chat_message():
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAIAgent(client=client, definition=definition)
    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.create_message",
    ):
        await agent.add_chat_message("threadId", ChatMessageContent(role="user", content="text"))  # pass anything


async def test_azure_ai_agent_invoke():
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAIAgent(client=client, definition=definition)
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


async def test_azure_ai_agent_invoke_stream():
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAIAgent(client=client, definition=definition)
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


def test_azure_ai_agent_get_channel_keys():
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAIAgent(client=client, definition=definition)
    keys = list(agent.get_channel_keys())
    assert len(keys) >= 3


async def test_azure_ai_agent_create_channel():
    client = AsyncMock(spec=AIProjectClient)
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAIAgent(client=client, definition=definition)
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
