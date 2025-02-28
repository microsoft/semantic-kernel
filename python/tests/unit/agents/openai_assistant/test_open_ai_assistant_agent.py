# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


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
        client=openai_client,
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
    with patch("semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings.OpenAISettings.create") as mock_create:
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
    "message",
    [
        pytest.param(ChatMessageContent(role=AuthorRole.USER, content="text")),
        pytest.param("text"),
    ],
)
async def test_open_ai_assistant_agent_add_chat_message(message, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.create_message",
    ):
        await agent.add_chat_message("threadId", message)


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_get_response(arguments, include_args, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        response = await agent.get_response("thread_id", **(kwargs or {}))

        assert response is not None
        assert response.content == "content"


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
        await agent.get_response("thread_id", **(kwargs or {}))


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_invoke(arguments, include_args, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
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
        async for item in agent.invoke("thread_id", **(kwargs or {})):
            results.append(item)

    assert len(results) == 1


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_invoke_stream(arguments, include_args, openai_client, assistant_definition):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)
    results = []

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    kwargs = None
    if include_args:
        kwargs = arguments

    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in agent.invoke_stream("thread_id", **(kwargs or {})):
            results.append(item)

    assert len(results) == 1


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


async def test_get_thread_messages(mock_thread_messages, openai_client, assistant_definition, openai_unit_test_env):
    agent = OpenAIAssistantAgent(client=openai_client, definition=assistant_definition)

    messages = [message async for message in agent.get_thread_messages("test_thread_id")]

    assert len(messages) == 2
    assert len(messages[0].items) == 3
    assert isinstance(messages[0].items[0], TextContent)
    assert isinstance(messages[0].items[1], AnnotationContent)
    assert isinstance(messages[0].items[2], AnnotationContent)
    assert messages[0].items[0].text == "Hello"

    assert len(messages[1].items) == 1
    assert isinstance(messages[1].items[0], FileReferenceContent)
    assert str(messages[1].items[0].file_id) == "test_file_id"
