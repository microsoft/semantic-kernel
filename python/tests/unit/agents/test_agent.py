# Copyright (c) Microsoft. All rights reserved.

import uuid
from unittest.mock import AsyncMock

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    def __init__(self, name: str = "Test-Agent", description: str = "A test agent", id: str = None):
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


async def test_agent_initialization():
    name = "TestAgent"
    description = "A test agent"
    id_value = str(uuid.uuid4())

    agent = MockAgent(name=name, description=description, id=id_value)

    assert agent.name == name
    assert agent.description == description
    assert agent.id == id_value


async def test_agent_default_id():
    agent = MockAgent()

    assert agent.id is not None
    assert isinstance(uuid.UUID(agent.id), uuid.UUID)


def test_get_channel_keys():
    agent = MockAgent()
    keys = agent.get_channel_keys()

    assert keys == ["key1", "key2"]


async def test_create_channel():
    agent = MockAgent()
    channel = await agent.create_channel()

    assert isinstance(channel, AgentChannel)


async def test_agent_equality():
    id_value = str(uuid.uuid4())

    agent1 = MockAgent(name="TestAgent", description="A test agent", id=id_value)
    agent2 = MockAgent(name="TestAgent", description="A test agent", id=id_value)

    assert agent1 == agent2

    agent3 = MockAgent(name="TestAgent", description="A different description", id=id_value)
    assert agent1 != agent3

    agent4 = MockAgent(name="AnotherAgent", description="A test agent", id=id_value)
    assert agent1 != agent4


async def test_agent_equality_different_type():
    agent = MockAgent(name="TestAgent", description="A test agent", id=str(uuid.uuid4()))
    non_agent = "Not an agent"

    assert agent != non_agent


async def test_agent_hash():
    id_value = str(uuid.uuid4())

    agent1 = MockAgent(name="TestAgent", description="A test agent", id=id_value)
    agent2 = MockAgent(name="TestAgent", description="A test agent", id=id_value)

    assert hash(agent1) == hash(agent2)

    agent3 = MockAgent(name="TestAgent", description="A different description", id=id_value)
    assert hash(agent1) != hash(agent3)
