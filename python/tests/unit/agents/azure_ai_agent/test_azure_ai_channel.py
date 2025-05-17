# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.projects.aio import AIProjectClient

from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.agents.azure_ai.azure_ai_channel import AzureAIChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


async def test_azure_ai_channel_invoke_invalid_agent():
    channel = AzureAIChannel(AsyncMock(spec=AIProjectClient), "thread123")
    with pytest.raises(AgentChatException):
        async for _ in channel.invoke(object()):
            pass


async def test_azure_ai_channel_invoke_valid_agent(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        channel = AzureAIChannel(ai_project_client, "thread123")
        results = []
        async for is_visible, msg in channel.invoke(agent):
            results.append((is_visible, msg))

    assert len(results) == 1


async def test_azure_ai_channel_invoke_stream_valid_agent(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        channel = AzureAIChannel(ai_project_client, "thread123")
        results = []
        async for is_visible, msg in channel.invoke_stream(agent, messages=[]):
            results.append((is_visible, msg))

    assert len(results) == 1


async def test_azure_ai_channel_get_history():
    # We need to return an async iterable, so let's do an AsyncMock returning an _async_gen
    class FakeAgentClient:
        delete_thread = AsyncMock()
        # We'll patch get_messages directly below

    class FakeClient:
        agents = FakeAgentClient()

    channel = AzureAIChannel(FakeClient(), "threadXYZ")

    async def fake_get_messages(client, thread_id):
        # Must produce an async iterable
        yield ChatMessageContent(role=AuthorRole.ASSISTANT, content="Previous msg")

    with patch(
        "semantic_kernel.agents.azure_ai.agent_thread_actions.AgentThreadActions.get_messages",
        new=fake_get_messages,  # direct replacement with a coroutine
    ):
        results = []
        async for item in channel.get_history():
            results.append(item)

    assert len(results) == 1
    assert results[0].content == "Previous msg"


# Helper for returning an async generator
async def _async_gen(items):
    for i in items:
        yield i
