# Copyright (c) Microsoft. All rights reserved.

import sys
import uuid
from typing import ClassVar
from unittest.mock import AsyncMock

import pytest

from semantic_kernel.agents.agent import AGENT_TYPE_REGISTRY, AgentRegistry, DeclarativeSpecMixin, register_agent_type
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException
from semantic_kernel.kernel import Kernel

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


# region Declarative Spec tests


class DummyPlugin:
    def __init__(self):
        self.functions = {"dummy_function": lambda: "result"}

    def get(self, name):
        return self.functions.get(name)


class DummyAgentSettings:
    azure_ai_search_connection_id = "test-conn-id"
    azure_ai_search_index_name = "test-index"


class DummyKernel:
    def __init__(self):
        self.plugins = {}

    def add_plugin(self, plugin):
        name = plugin.__class__.__name__
        self.plugins[name] = plugin


async def test_resolve_placeholders_with_short_and_long_keys():
    class DummyDeclarativeSpec:
        @classmethod
        def resolve_placeholders(cls, yaml_str, settings=None, extras=None):
            import re

            pattern = re.compile(r"\$\{([^}]+)\}")
            field_mapping = {
                "AzureAISearchConnectionId": "conn-123",
                "AzureAI:AzureAISearchConnectionId": "conn-123-override",
            }
            if extras:
                field_mapping.update(extras)

            def replacer(match):
                full_key = match.group(1)
                section, _, key = full_key.partition(":")
                if section != "AzureAI":
                    return match.group(0)
                return str(field_mapping.get(key) or field_mapping.get(full_key) or match.group(0))

            return pattern.sub(replacer, yaml_str)

    spec = "connection: ${AzureAI:AzureAISearchConnectionId}"
    resolved = DummyDeclarativeSpec.resolve_placeholders(spec)
    assert resolved == "connection: conn-123"


async def test_validate_tools_succeeds_with_valid_plugin():
    class DummyDeclarativeSpec:
        @classmethod
        def _validate_tools(cls, tools_list, kernel):
            for tool in tools_list:
                tool_id = tool.get("id")
                if not tool_id or tool.get("type") != "function":
                    continue
                plugin_name, function_name = tool_id.split(".")
                plugin = kernel.plugins.get(plugin_name)
                if not plugin:
                    raise ValueError(f"Plugin {plugin_name} missing")
                if function_name not in plugin.functions:
                    raise ValueError(f"Function {function_name} missing in plugin {plugin_name}")

    kernel = DummyKernel()
    plugin = DummyPlugin()
    kernel.add_plugin(plugin)

    DummyDeclarativeSpec._validate_tools([{"id": "DummyPlugin.dummy_function", "type": "function"}], kernel)


async def test_validate_tools_raises_on_missing_plugin():
    class DummyDeclarativeSpec:
        @classmethod
        def _validate_tools(cls, tools_list, kernel):
            for tool in tools_list:
                tool_id = tool.get("id")
                if not tool_id or tool.get("type") != "function":
                    continue
                plugin_name, function_name = tool_id.split(".")
                plugin = kernel.plugins.get(plugin_name)
                if not plugin:
                    raise ValueError(f"Plugin {plugin_name} missing")
                if function_name not in plugin.functions:
                    raise ValueError(f"Function {function_name} missing in plugin {plugin_name}")

    kernel = DummyKernel()

    with pytest.raises(ValueError, match="Plugin DummyPlugin missing"):
        DummyDeclarativeSpec._validate_tools([{"id": "DummyPlugin.dummy_function", "type": "function"}], kernel)


def test_normalize_spec_fields_creates_kernel_and_extracts_fields():
    data = {
        "name": "TestAgent",
        "description": "An agent",
        "instructions": "Use this.",
        "model": {"options": {"temperature": 0.7}},
    }

    fields, kernel = DeclarativeSpecMixin._normalize_spec_fields(data)
    assert isinstance(kernel, Kernel)
    assert fields["name"] == "TestAgent"
    assert isinstance(fields["arguments"], KernelArguments)


def test_normalize_spec_fields_adds_plugins_to_kernel():
    plugin = DummyPlugin()
    data = {"name": "PluginAgent"}

    _, kernel = DeclarativeSpecMixin._normalize_spec_fields(data, plugins=[plugin])
    assert "DummyPlugin" in kernel.plugins


def test_normalize_spec_fields_parses_prompt_template_and_overwrites_instructions():
    data = {"name": "T", "prompt_template": {"template": "new instructions", "template_format": "semantic-kernel"}}

    fields, _ = DeclarativeSpecMixin._normalize_spec_fields(data)
    assert fields["instructions"] == "new instructions"


def test_validate_tools_success(custom_plugin_class):
    kernel = Kernel()
    kernel.add_plugin(custom_plugin_class())
    tools_list = [{"id": "CustomPlugin.getLightStatus", "type": "function"}]

    DeclarativeSpecMixin._validate_tools(tools_list, kernel)


def test_validate_tools_fails_on_invalid_format():
    kernel = Kernel()
    with pytest.raises(AgentInitializationException, match="format"):
        DeclarativeSpecMixin._validate_tools([{"id": "badformat", "type": "function"}], kernel)


def test_validate_tools_fails_on_missing_plugin():
    kernel = Kernel()
    with pytest.raises(AgentInitializationException, match="not found in kernel"):
        DeclarativeSpecMixin._validate_tools([{"id": "MissingPlugin.foo", "type": "function"}], kernel)


def test_validate_tools_fails_on_missing_function():
    plugin = DummyPlugin()
    kernel = Kernel()
    kernel.add_plugin(plugin)
    with pytest.raises(AgentInitializationException, match="not found in plugin"):
        DeclarativeSpecMixin._validate_tools([{"id": "DummyPlugin.bar", "type": "function"}], kernel)


@register_agent_type("test_agent")
class TestAgent(DeclarativeSpecMixin, Agent):
    @classmethod
    def resolve_placeholders(cls, yaml_str, settings=None, extras=None):
        return yaml_str

    @classmethod
    async def _from_dict(cls, data, kernel, **kwargs):
        return cls(
            name=data.get("name"),
            description=data.get("description"),
            instructions=data.get("instructions"),
            kernel=kernel,
        )

    async def get_response(self, messages, instructions_override=None):
        return "Test response"

    async def invoke(self, messages, **kwargs):
        return "invoke result"

    async def invoke_stream(self, messages, **kwargs):
        yield "streamed result"


async def test_register_type_and_create_from_yaml_success():
    yaml_str = """
type: test_agent
name: TestAgent
"""
    agent = await AgentRegistry.create_from_yaml(yaml_str)
    assert agent.__class__.__name__ == "TestAgent"


async def test_create_from_yaml_missing_type():
    yaml_str = """
name: InvalidAgent
"""
    with pytest.raises(AgentInitializationException, match="Missing 'type'"):
        await AgentRegistry.create_from_yaml(yaml_str)


async def test_create_from_yaml_unregistered_type():
    yaml_str = """
type: nonexistent_agent
"""
    # Ensure unregistered
    AGENT_TYPE_REGISTRY.pop("nonexistent_agent", None)
    with pytest.raises(AgentInitializationException, match="not registered"):
        await AgentRegistry.create_from_yaml(yaml_str)


async def test_create_from_dict_success(test_agent_cls):
    data = {"type": "test_agent", "name": "FromDictAgent"}
    agent: TestAgent = await AgentRegistry.create_from_dict(data)
    assert agent.name == "FromDictAgent"
    assert type(agent).__name__ == "TestAgent"


async def test_create_from_dict_missing_type():
    data = {"name": "NoType"}
    with pytest.raises(AgentInitializationException, match="Missing 'type'"):
        await AgentRegistry.create_from_dict(data)


async def test_create_from_dict_type_not_supported():
    AGENT_TYPE_REGISTRY.pop("unknown", None)
    data = {"type": "unknown"}
    with pytest.raises(AgentInitializationException, match="not supported"):
        await AgentRegistry.create_from_dict(data)


async def test_create_from_file_reads_and_creates(tmp_path, test_agent_cls):
    file_path = tmp_path / "spec.yaml"
    file_path.write_text("type: test_agent\nname: FileAgent\n", encoding="utf-8")

    agent: TestAgent = await AgentRegistry.create_from_file(str(file_path))
    assert agent.name == "FileAgent"
    assert type(agent).__name__ == "TestAgent"


async def test_create_from_file_raises_on_bad_path():
    with pytest.raises(AgentInitializationException, match="Failed to read agent spec file"):
        await AgentRegistry.create_from_file("/nonexistent/path/spec.yaml")


# endregion
