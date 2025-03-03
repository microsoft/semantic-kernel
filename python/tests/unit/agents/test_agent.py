# Copyright (c) Microsoft. All rights reserved.

import sys
import uuid
from typing import ClassVar
from unittest.mock import AsyncMock

import pytest

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.functions.kernel_arguments import KernelArguments


class MockChatHistory:
    """Minimal mock for ChatHistory to hold messages."""

    def __init__(self, messages=None):
        self.messages = messages if messages is not None else []


class MockChannel(AgentChannel):
    """Mock channel for testing get_channel_keys and create_channel."""


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    channel_type: ClassVar[type[AgentChannel]] = MockChannel

    def __init__(self, name: str = "Test-Agent", description: str = "A test agent", id: str = None):
        args = {
            "name": name,
            "description": description,
        }
        if id is not None:
            args["id"] = id
        super().__init__(**args)

    async def create_channel(self) -> AgentChannel:
        return AsyncMock(spec=AgentChannel)

    @override
    async def get_response(self, *args, **kwargs):
        raise NotImplementedError

    @override
    async def invoke(self, *args, **kwargs):
        raise NotImplementedError

    @override
    async def invoke_stream(self, *args, **kwargs):
        raise NotImplementedError


class MockAgentWithoutChannelType(MockAgent):
    channel_type = None


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

    assert len(list(keys)) == 1, "Should return a single key"


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


def test_get_channel_keys_no_channel_type():
    agent = MockAgentWithoutChannelType()
    with pytest.raises(NotImplementedError):
        list(agent.get_channel_keys())


def test_merge_arguments_both_none():
    agent = MockAgent()
    merged = agent._merge_arguments(None)
    assert isinstance(merged, KernelArguments)
    assert len(merged) == 0, "If both arguments are None, should return an empty KernelArguments object"


def test_merge_arguments_agent_none_override_not_none():
    agent = MockAgent()
    override = KernelArguments(settings={"key": "override"}, param1="val1")

    merged = agent._merge_arguments(override)
    assert merged is override, "If agent.arguments is None, just return override_args"


def test_merge_arguments_override_none_agent_not_none():
    agent = MockAgent()
    agent.arguments = KernelArguments(settings={"key": "base"}, param1="baseVal")

    merged = agent._merge_arguments(None)
    assert merged is agent.arguments, "If override_args is None, should return the agent's arguments"


def test_merge_arguments_both_not_none():
    agent = MockAgent()
    agent.arguments = KernelArguments(settings={"key1": "val1", "common": "base"}, param1="baseVal")
    override = KernelArguments(settings={"key2": "override_val", "common": "override"}, param2="override_param")

    merged = agent._merge_arguments(override)

    assert merged.execution_settings["key1"] == "val1", "Should retain original setting from agent"
    assert merged.execution_settings["key2"] == "override_val", "Should include new setting from override"
    assert merged.execution_settings["common"] == "override", "Override should take precedence"

    assert merged["param1"] == "baseVal", "Should retain base param from agent"
    assert merged["param2"] == "override_param", "Should include param from override"
