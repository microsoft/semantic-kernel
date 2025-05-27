# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from semantic_kernel.agents import AgentRegistry
from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent, ResponsesAgentThread
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.fixture
def mock_openai_client():
    return AsyncMock(spec=AsyncOpenAI)


class SamplePlugin:
    @kernel_function
    def test_plugin(self, *args, **kwargs):
        pass


class ResponseModelPydantic(BaseModel):
    response: str
    items: list[str]


class ResponseModelNonPydantic:
    response: str
    items: list[str]


async def test_open_ai_assistant_agent_init():
    sample_prompt_template_config = PromptTemplateConfig(
        template="template",
    )

    kernel_plugin = KernelPlugin(name="expected_plugin_name", description="expected_plugin_description")

    agent = OpenAIResponsesAgent(
        ai_model_id="model_id",
        id="agent123",
        name="agentName",
        description="desc",
        client=AsyncMock(spec=AsyncOpenAI),
        arguments=KernelArguments(test="test"),
        kernel=AsyncMock(spec=Kernel),
        plugins=[SamplePlugin(), kernel_plugin],
        polling_options=AsyncMock(spec=RunPollingOptions),
        prompt_template_config=sample_prompt_template_config,
        other_arg="test",
    )
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"


def test_open_ai_settings_create_throws(openai_unit_test_env):
    with patch(
        "semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings.OpenAISettings.__init__"
    ) as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationException, match="Failed to create OpenAI settings."):
            _, _ = OpenAIResponsesAgent.setup_resources(api_key="test_api_key")


def test_open_ai_assistant_with_file_search_tool():
    tools, resources = OpenAIResponsesAgent.configure_file_search_tool(vector_store_ids=["vector_store_id"])
    assert tools is not None
    assert resources is not None


@pytest.mark.parametrize(
    "model, json_schema_expected",
    [
        pytest.param(ResponseModelPydantic, True),
        pytest.param(ResponseModelNonPydantic, True),
        pytest.param({"type": "json_object"}, False),
        pytest.param({"type": "json_schema", "json_schema": {"schema": {}}}, False),
    ],
)
def test_configure_response_format(model, json_schema_expected):
    response_format = OpenAIResponsesAgent.configure_response_format(model)
    assert response_format is not None
    if json_schema_expected:
        assert response_format["format"]["schema"] is not None  # type: ignore


def test_configure_response_format_unexpected_type():
    with pytest.raises(AgentInitializationException) as exc_info:
        OpenAIResponsesAgent.configure_response_format({"type": "invalid_type"})
    assert "Encountered unexpected response_format type" in str(exc_info.value)


def test_configure_response_format_json_schema_invalid_schema():
    with pytest.raises(AgentInitializationException) as exc_info:
        OpenAIResponsesAgent.configure_response_format({"type": "json_schema", "json_schema": "not_a_dict"})
    assert "If response_format has type 'json_schema'" in str(exc_info.value)


def test_configure_response_format_invalid_input_type():
    with pytest.raises(AgentInitializationException) as exc_info:
        OpenAIResponsesAgent.configure_response_format(3)  # type: ignore
    assert "response_format must be a dictionary" in str(exc_info.value)


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_openai_responses_agent_get_response(arguments, include_args):
    agent = OpenAIResponsesAgent(client=AsyncMock(spec=AsyncOpenAI), ai_model_id="model_id")

    mock_thread = AsyncMock(spec=ResponsesAgentThread)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.responses_agent_thread_actions.ResponsesAgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        response = await agent.get_response(messages="test", thread=mock_thread, **(kwargs or {}))

        assert response is not None
        assert response.message.content == "content"
        assert response.thread is not None


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_openai_responses_agent_get_response_exception(arguments, include_args):
    agent = OpenAIResponsesAgent(client=AsyncMock(spec=AsyncOpenAI), ai_model_id="model_id")

    mock_thread = AsyncMock(spec=ResponsesAgentThread)

    async def fake_invoke(*args, **kwargs):
        yield False, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with (
        patch(
            "semantic_kernel.agents.open_ai.responses_agent_thread_actions.ResponsesAgentThreadActions.invoke",
            side_effect=fake_invoke,
        ),
        pytest.raises(AgentInvokeException),
    ):
        await agent.get_response(messages="test", thread=mock_thread, **(kwargs or {}))


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_openai_responses_agent_invoke(arguments, include_args):
    agent = OpenAIResponsesAgent(client=AsyncMock(spec=AsyncOpenAI), ai_model_id="model_id")
    mock_thread = AsyncMock(spec=ResponsesAgentThread)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.responses_agent_thread_actions.ResponsesAgentThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke(messages="test", thread=mock_thread, **(kwargs or {})):
            results.append(item)

    assert len(results) == 1


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_openai_responses_agent_invoke_stream(arguments, include_args):
    agent = OpenAIResponsesAgent(client=AsyncMock(spec=AsyncOpenAI), ai_model_id="model_id")
    mock_thread = AsyncMock(spec=ResponsesAgentThread)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.responses_agent_thread_actions.ResponsesAgentThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream(messages="test", thread=mock_thread, **(kwargs or {})):
            results.append(item)

    assert len(results) == 1


def test_create_openai_client(openai_unit_test_env):
    client, model = OpenAIResponsesAgent.setup_resources(env_file_path="./", default_headers={"user_agent": "test"})
    assert client is not None
    assert client.api_key == "test_api_key"
    assert model is not None


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
async def test_open_ai_agent_missing_api_key_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The OpenAI API key is required."):
        _, _ = OpenAIResponsesAgent.setup_resources(env_file_path="./", default_headers={"user_agent": "test"})


@pytest.mark.parametrize("exclude_list", [["OPENAI_RESPONSES_MODEL_ID"]], indirect=True)
async def test_open_ai_agent_missing_chat_deployment_name_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The OpenAI Responses model ID is required."):
        _, _ = OpenAIResponsesAgent.setup_resources(
            env_file_path="./",
            api_key="test_api_key",
            default_headers={"user_agent": "test"},
        )


async def test_openai_assistant_agent_from_yaml_minimal(openai_unit_test_env, mock_openai_client):
    spec = """
type: openai_responses
name: MinimalAgent
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
"""
    client = mock_openai_client
    agent: OpenAIResponsesAgent = await AgentRegistry.create_from_yaml(spec, client=client)
    assert isinstance(agent, OpenAIResponsesAgent)
    assert agent.name == "MinimalAgent"
    assert agent.ai_model_id == openai_unit_test_env.get("OPENAI_RESPONSES_MODEL_ID")


async def test_openai_assistant_agent_with_tools(openai_unit_test_env, mock_openai_client):
    spec = """
type: openai_responses
name: FileSearchAgent
description: Uses file search.
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
tools:
  - type: file_search
    description: File search for document retrieval.
    options:
      vector_store_ids:
        - ${OpenAI:VectorStoreId}
"""
    client = mock_openai_client
    agent: OpenAIResponsesAgent = await AgentRegistry.create_from_yaml(
        spec, client=client, extras={"OpenAI:VectorStoreId": "vector-store-123"}
    )
    assert agent.name == "FileSearchAgent"
    assert any(t["type"] == "file_search" for t in agent.tools)


async def test_openai_assistant_agent_with_inputs_outputs_template(openai_unit_test_env, mock_openai_client):
    spec = """
type: openai_responses
name: StoryAgent
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
inputs:
  topic:
    description: The story topic.
    required: true
    default: AI
  length:
    description: The length of story.
    required: true
    default: 2
outputs:
  output1:
    description: The story.
template:
  format: semantic-kernel
"""
    client = mock_openai_client
    agent: OpenAIResponsesAgent = await AgentRegistry.create_from_yaml(spec, client=client)
    assert agent.name == "StoryAgent"
    assert agent.prompt_template.prompt_template_config.template_format == "semantic-kernel"


async def test_openai_assistant_agent_from_dict_missing_type():
    data = {"name": "NoType"}
    with pytest.raises(AgentInitializationException, match="Missing 'type'"):
        await AgentRegistry.create_from_dict(data)


async def test_openai_assistant_agent_from_yaml_missing_required_fields():
    spec = """
type: openai_responses
"""
    with pytest.raises(AgentInitializationException):
        await AgentRegistry.create_from_yaml(spec)


async def test_agent_from_file_success(tmp_path, openai_unit_test_env, mock_openai_client):
    file_path = tmp_path / "spec.yaml"
    file_path.write_text(
        """
type: openai_responses
name: DeclarativeAgent
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
""",
        encoding="utf-8",
    )
    client = mock_openai_client
    agent: OpenAIResponsesAgent = await AgentRegistry.create_from_file(str(file_path), client=client)
    assert agent.name == "DeclarativeAgent"
    assert isinstance(agent, OpenAIResponsesAgent)


async def test_openai_assistant_agent_from_yaml_invalid_type():
    spec = """
type: not_registered
name: ShouldFail
"""
    with pytest.raises(AgentInitializationException, match="not registered"):
        await AgentRegistry.create_from_yaml(spec)
