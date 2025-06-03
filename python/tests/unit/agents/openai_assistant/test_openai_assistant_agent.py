# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant
from pydantic import BaseModel, ValidationError

from semantic_kernel.agents import AgentRegistry, AgentResponseItem, OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.openai_assistant_agent import AssistantAgentThread
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.fixture
def mock_openai_client_and_definition():
    client = AsyncMock(spec=AsyncOpenAI)
    client.beta = MagicMock()
    client.beta.assistants = MagicMock()

    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "DeclarativeAgent"
    definition.description = "desc"
    definition.instructions = "test agent"
    definition.tools = []
    definition.model = "gpt-4o"
    definition.temperature = 1.0
    definition.top_p = 1.0
    definition.metadata = {}

    client.beta.assistants.create = AsyncMock(return_value=definition)

    return client, definition


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


async def test_open_ai_assistant_agent_init(openai_client, assistant_definition):
    sample_prompt_template_config = PromptTemplateConfig(
        template="template",
    )

    kernel_plugin = KernelPlugin(name="expected_plugin_name", description="expected_plugin_description")

    agent = OpenAIAssistantAgent(
        client=AsyncMock(spec=AsyncOpenAI),
        definition=assistant_definition,
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
            _, _ = OpenAIAssistantAgent.setup_resources(api_key="test_api_key")


def test_open_ai_assistant_with_code_interpreter_tool():
    tools, resources = OpenAIAssistantAgent.configure_code_interpreter_tool(file_ids=["file_id"])
    assert tools is not None
    assert resources is not None


def test_open_ai_assistant_with_file_search_tool():
    tools, resources = OpenAIAssistantAgent.configure_file_search_tool(vector_store_ids=["vector_store_id"])
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
    response_format = OpenAIAssistantAgent.configure_response_format(model)
    assert response_format is not None
    if json_schema_expected:
        assert response_format["json_schema"] is not None  # type: ignore


def test_configure_response_format_unexpected_type():
    with pytest.raises(AgentInitializationException) as exc_info:
        OpenAIAssistantAgent.configure_response_format({"type": "invalid_type"})
    assert "Encountered unexpected response_format type" in str(exc_info.value)


def test_configure_response_format_json_schema_invalid_schema():
    with pytest.raises(AgentInitializationException) as exc_info:
        OpenAIAssistantAgent.configure_response_format({"type": "json_schema", "json_schema": "not_a_dict"})
    assert "If response_format has type 'json_schema'" in str(exc_info.value)


def test_configure_response_format_invalid_input_type():
    with pytest.raises(AgentInitializationException) as exc_info:
        OpenAIAssistantAgent.configure_response_format(3)  # type: ignore
    assert "response_format must be a dictionary" in str(exc_info.value)


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_get_response(arguments, include_args, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)

    mock_thread = AsyncMock(spec=AssistantAgentThread)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke",
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
async def test_open_ai_assistant_agent_get_response_exception(
    arguments, include_args, openai_client, assistant_definition
):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)

    mock_thread = AsyncMock(spec=AssistantAgentThread)

    async def fake_invoke(*args, **kwargs):
        yield False, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with (
        patch(
            "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke",
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
async def test_open_ai_assistant_agent_invoke(arguments, include_args, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    mock_thread = AsyncMock(spec=AssistantAgentThread)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke(messages="test", thread=mock_thread, **(kwargs or {})):
            results.append(item)

    assert len(results) == 1


async def test_open_ai_assistant_agent_invoke_message_ordering(openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    mock_thread = AsyncMock(spec=AssistantAgentThread)

    tool_call_msg = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        content="",
        items=[FunctionCallContent(name="ToolA", arguments="{}")],
    )
    tool_result_msg = ChatMessageContent(
        role=AuthorRole.ASSISTANT,
        content="",
        items=[FunctionResultContent(name="ToolA", result="$9.99", id="func_1")],
    )
    assistant_msg = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Here is your answer.")

    emitted_callback_messages = []
    yielded_messages = []

    async def on_intermediate_message(msg: ChatMessageContent):
        emitted_callback_messages.append(msg)

    async def fake_invoke(*args, **kwargs):
        yield False, tool_call_msg
        yield False, tool_result_msg
        yield True, assistant_msg

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke(
            messages="test", thread=mock_thread, on_intermediate_message=on_intermediate_message
        ):
            yielded_messages.append(item)

    assert emitted_callback_messages == [tool_call_msg, tool_result_msg]
    assert yielded_messages == [AgentResponseItem(message=assistant_msg, thread=mock_thread)]


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_invoke_stream(arguments, include_args, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    mock_thread = AsyncMock(spec=AssistantAgentThread)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream(messages="test", thread=mock_thread, **(kwargs or {})):
            results.append(item)

    assert len(results) == 1


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_invoke_stream_with_on_new_message_callback(
    arguments, include_args, openai_client, assistant_definition
):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    mock_thread = AsyncMock(spec=AssistantAgentThread)
    results = []

    final_chat_history = ChatHistory()

    async def handle_stream_completion(message: ChatMessageContent) -> None:
        final_chat_history.add_message(message)

    tool_msg = ChatMessageContent(
        role=AuthorRole.ASSISTANT, content="", items=[FunctionCallContent(name="ToolA", arguments="{}")]
    )

    streamed_msg = StreamingChatMessageContent(role=AuthorRole.ASSISTANT, content="fake content", choice_index=0)

    async def fake_invoke(*args, output_messages=None, **kwargs):
        if output_messages is not None:
            output_messages.append(tool_msg)
        yield streamed_msg

    kwargs = arguments if include_args else {}

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream(
            messages="test", thread=mock_thread, on_intermediate_message=handle_stream_completion, **kwargs
        ):
            results.append(item)

    assert len(results) == 1
    assert results[0].message.content == "fake content"

    assert len(final_chat_history.messages) == 1
    assert final_chat_history.messages[0] == tool_msg


def test_open_ai_assistant_agent_get_channel_keys(openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    keys = list(agent.get_channel_keys())
    assert len(keys) >= 3


async def test_open_ai_assistant_agent_create_channel(openai_client, assistant_definition):
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    ch = await agent.create_channel()
    assert isinstance(ch, OpenAIAssistantChannel)
    assert ch.thread_id == "test_thread_id"


def test_create_openai_client(openai_unit_test_env):
    client, model = OpenAIAssistantAgent.setup_resources(env_file_path="./", default_headers={"user_agent": "test"})
    assert client is not None
    assert client.api_key == "test_api_key"
    assert model is not None


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
async def test_open_ai_agent_missing_api_key_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The OpenAI API key is required."):
        _, _ = OpenAIAssistantAgent.setup_resources(env_file_path="./", default_headers={"user_agent": "test"})


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
async def test_open_ai_agent_missing_chat_deployment_name_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The OpenAI model ID is required."):
        _, _ = OpenAIAssistantAgent.setup_resources(
            env_file_path="./",
            api_key="test_api_key",
            default_headers={"user_agent": "test"},
        )


async def test_openai_assistant_agent_from_yaml_minimal(openai_unit_test_env, mock_openai_client_and_definition):
    spec = """
type: openai_assistant
name: MinimalAgent
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
"""
    client, definition = mock_openai_client_and_definition
    definition.name = "MinimalAgent"
    agent = await AgentRegistry.create_from_yaml(spec, client=client)
    assert isinstance(agent, OpenAIAssistantAgent)
    assert agent.name == "MinimalAgent"
    assert agent.definition.model == "gpt-4o"


async def test_openai_assistant_agent_with_tools(openai_unit_test_env, mock_openai_client_and_definition):
    spec = """
type: openai_assistant
name: CodeAgent
description: Uses code interpreter.
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
tools:
  - type: code_interpreter
    options:
      file_ids:
        - ${OpenAI:FileId1}
"""
    client, definition = mock_openai_client_and_definition
    definition.name = "CodeAgent"
    definition.tools = [{"type": "code_interpreter", "options": {"file_ids": ["file-123"]}}]
    agent = await AgentRegistry.create_from_yaml(spec, client=client, extras={"OpenAI:FileId1": "file-123"})
    assert agent.name == "CodeAgent"
    assert any(t["type"] == "code_interpreter" for t in agent.definition.tools)


async def test_openai_assistant_agent_with_inputs_outputs_template(
    openai_unit_test_env, mock_openai_client_and_definition
):
    spec = """
type: openai_assistant
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
    client, definition = mock_openai_client_and_definition
    definition.name = "StoryAgent"
    agent: OpenAIAssistantAgent = await AgentRegistry.create_from_yaml(spec, client=client)
    assert agent.name == "StoryAgent"
    assert agent.prompt_template.prompt_template_config.template_format == "semantic-kernel"


async def test_openai_assistant_agent_from_dict_missing_type():
    data = {"name": "NoType"}
    with pytest.raises(AgentInitializationException, match="Missing 'type'"):
        await AgentRegistry.create_from_dict(data)


async def test_openai_assistant_agent_from_yaml_missing_required_fields():
    spec = """
type: openai_assistant
"""
    with pytest.raises(AgentInitializationException):
        await AgentRegistry.create_from_yaml(spec)


async def test_agent_from_file_success(tmp_path, openai_unit_test_env, mock_openai_client_and_definition):
    file_path = tmp_path / "spec.yaml"
    file_path.write_text(
        """
type: openai_assistant
name: DeclarativeAgent
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
""",
        encoding="utf-8",
    )
    client, _ = mock_openai_client_and_definition
    agent = await AgentRegistry.create_from_file(str(file_path), client=client)
    assert agent.name == "DeclarativeAgent"
    assert isinstance(agent, OpenAIAssistantAgent)


async def test_openai_assistant_agent_from_yaml_invalid_type():
    spec = """
type: not_registered
name: ShouldFail
"""
    with pytest.raises(AgentInitializationException, match="not registered"):
        await AgentRegistry.create_from_yaml(spec)
