# Copyright (c) Microsoft. All rights reserved.

import uuid
from unittest.mock import AsyncMock

import pytest

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.agent_channel import AgentChannel


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    def __init__(self, name: str = "Test Agent", description: str = "A test agent", id: str = None):
        args = {
            "name": name,
            "description": description,
        }
        if id is not None:
            args["id"] = id
        super().__init__(**args)

    def get_channel_keys(self) -> list[str]:
        return ["key1", "key2"]

    async def create_channel(self) -> AgentChannel:
        return AsyncMock(spec=AgentChannel)


@pytest.mark.asyncio
async def test_agent_initialization():
    name = "Test Agent"
    description = "A test agent"
    id_value = str(uuid.uuid4())

    agent = MockAgent(name=name, description=description, id=id_value)

    assert agent.name == name
    assert agent.description == description
    assert agent.id == id_value


@pytest.mark.asyncio
async def test_agent_default_id():
    agent = MockAgent()

    assert agent.id is not None
    assert isinstance(uuid.UUID(agent.id), uuid.UUID)


def test_get_channel_keys():
    agent = MockAgent()
    keys = agent.get_channel_keys()

    assert keys == ["key1", "key2"]


@pytest.mark.asyncio
async def test_create_channel():
    agent = MockAgent()
    channel = await agent.create_channel()

    assert isinstance(channel, AgentChannel)
