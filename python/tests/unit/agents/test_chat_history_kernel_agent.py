# Copyright (c) Microsoft. All rights reserved.

import uuid
from collections.abc import AsyncIterable

from semantic_kernel.agents.chat_history_channel import ChatHistoryChannel
from semantic_kernel.agents.chat_history_kernel_agent import ChatHistoryKernelAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


class MockChatHistoryKernelAgent(ChatHistoryKernelAgent):
    def __init__(
        self,
        service_id: str = "test_service",
        name: str = "Test Agent",
        instructions: str = "Test Instructions",
        id: str = None,
        description: str = "Test Description",
    ):
        super().__init__(service_id=service_id, name=name, instructions=instructions, id=id, description=description)

    async def invoke(self, history: list[ChatMessageContent]) -> AsyncIterable[ChatMessageContent]:
        for message in history:
            yield ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")

    async def invoke_stream(self, history: list[ChatMessageContent]) -> AsyncIterable[StreamingChatMessageContent]:
        pass


def test_initialization():
    name = "Test Agent"
    instructions = "These are the instructions"
    id_value = str(uuid.uuid4())
    description = "This is a test agent"

    agent = MockChatHistoryKernelAgent(name=name, instructions=instructions, id=id_value, description=description)

    assert agent.name == name
    assert agent.instructions == instructions
    assert agent.id == id_value
    assert agent.description == description


def test_default_id():
    agent = MockChatHistoryKernelAgent()

    assert agent.id is not None
    assert isinstance(uuid.UUID(agent.id), uuid.UUID)


def test_get_channel_keys():
    agent = MockChatHistoryKernelAgent()
    keys = agent.get_channel_keys()

    assert keys == [ChatHistoryChannel.__name__]


def test_create_channel():
    agent = MockChatHistoryKernelAgent()
    channel = agent.create_channel()

    assert isinstance(channel, ChatHistoryChannel)
