# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock

from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


async def test_agent_thread_actions_create_thread():
    class FakeAgentClient:
        create_thread = AsyncMock(return_value=type("FakeThread", (), {"id": "thread123"}))

    class FakeClient:
        agents = FakeAgentClient()

    client = FakeClient()
    thread_id = await AgentThreadActions.create_thread(client)
    assert thread_id == "thread123"


async def test_agent_thread_actions_create_message():
    class FakeAgentClient:
        create_message = AsyncMock(return_value="someMessage")

    class FakeClient:
        agents = FakeAgentClient()

    msg = ChatMessageContent(role=AuthorRole.USER, content="some content")
    out = await AgentThreadActions.create_message(FakeClient(), "threadXYZ", msg)
    assert out == "someMessage"


async def test_agent_thread_actions_create_message_no_content():
    class FakeAgentClient:
        create_message = AsyncMock(return_value="should_not_be_called")

    class FakeClient:
        agents = FakeAgentClient()

    message = ChatMessageContent(role=AuthorRole.USER, content="   ")
    out = await AgentThreadActions.create_message(FakeClient(), "threadXYZ", message)
    assert out is None
    assert FakeAgentClient.create_message.await_count == 0
