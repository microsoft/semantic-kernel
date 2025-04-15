# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads.file_citation_annotation import FileCitation, FileCitationAnnotation
from openai.types.beta.threads.file_path_annotation import FilePath, FilePathAnnotation
from openai.types.beta.threads.image_file import ImageFile
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.text import Text
from openai.types.beta.threads.text_content_block import TextContentBlock
from pydantic import BaseModel, ValidationError

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_agent import AssistantAgentThread
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException
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


@pytest.fixture
def mock_thread_messages():
    class MockMessage:
        def __init__(self, id, role, content, assistant_id=None):
            self.id = id
            self.role = role
            self.content = content
            self.assistant_id = assistant_id

    return [
        MockMessage(
            id="test_message_id_1",
            role="user",
            content=[
                TextContentBlock(
                    type="text",
                    text=Text(
                        value="Hello",
                        annotations=[
                            FilePathAnnotation(
                                type="file_path",
                                file_path=FilePath(file_id="test_file_id"),
                                end_index=5,
                                start_index=0,
                                text="Hello",
                            ),
                            FileCitationAnnotation(
                                type="file_citation",
                                file_citation=FileCitation(file_id="test_file_id"),
                                text="Hello",
                                start_index=0,
                                end_index=5,
                            ),
                        ],
                    ),
                )
            ],
        ),
        MockMessage(
            id="test_message_id_2",
            role="assistant",
            content=[
                ImageFileContentBlock(type="image_file", image_file=ImageFile(file_id="test_file_id", detail="auto"))
            ],
            assistant_id="assistant_1",
        ),
    ]


async def test_open_ai_assistant_agent_init():
    sample_prompt_template_config = PromptTemplateConfig(
        template="template",
    )

    kernel_plugin = KernelPlugin(name="expected_plugin_name", description="expected_plugin_description")

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
        arguments=KernelArguments(test="test"),
        kernel=AsyncMock(spec=Kernel),
        plugins=[SamplePlugin(), kernel_plugin],
        polling_options=AsyncMock(spec=RunPollingOptions),
        prompt_template_config=sample_prompt_template_config,  # type: ignore
        other_arg="test",  # type: ignore
    )
    assert agent.id == "agent123"
    assert agent.name == "agentName"
    assert agent.description == "desc"


def test_azure_open_ai_settings_create_throws(azure_openai_unit_test_env):
    with patch(
        "semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings.AzureOpenAISettings.__init__"
    ) as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationException, match="Failed to create Azure OpenAI settings."):
            _, _ = AzureAssistantAgent.setup_resources(api_key="test_api_key")


def test_open_ai_assistant_with_code_interpreter_tool():
    tools, resources = AzureAssistantAgent.configure_code_interpreter_tool(file_ids=["file_id"])
    assert tools is not None
    assert resources is not None


def test_open_ai_assistant_with_file_search_tool():
    tools, resources = AzureAssistantAgent.configure_file_search_tool(vector_store_ids=["vector_store_id"])
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
    response_format = AzureAssistantAgent.configure_response_format(model)
    assert response_format is not None
    if json_schema_expected:
        assert response_format["json_schema"] is not None  # type: ignore


def test_configure_response_format_unexpected_type():
    with pytest.raises(AgentInitializationException) as exc_info:
        AzureAssistantAgent.configure_response_format({"type": "invalid_type"})
    assert "Encountered unexpected response_format type" in str(exc_info.value)


def test_configure_response_format_json_schema_invalid_schema():
    with pytest.raises(AgentInitializationException) as exc_info:
        AzureAssistantAgent.configure_response_format({"type": "json_schema", "json_schema": "not_a_dict"})
    assert "If response_format has type 'json_schema'" in str(exc_info.value)


def test_configure_response_format_invalid_input_type():
    with pytest.raises(AgentInitializationException) as exc_info:
        AzureAssistantAgent.configure_response_format(3)  # type: ignore
    assert "response_format must be a dictionary" in str(exc_info.value)


@pytest.mark.parametrize(
    "message",
    [
        pytest.param(ChatMessageContent(role=AuthorRole.USER, content="text")),
        pytest.param("text"),
    ],
)
async def test_open_ai_assistant_agent_add_chat_message(message):
    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAssistantAgent(client=client, definition=definition)
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
async def test_open_ai_assistant_agent_invoke(arguments, include_args):
    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    definition.tools = []
    definition.model = "gpt-4o"
    definition.response_format = {"type": "json_object"}
    definition.temperature = 0.1
    definition.top_p = 0.9
    definition.metadata = {}
    agent = AzureAssistantAgent(client=client, definition=definition)
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


@pytest.mark.parametrize(
    "arguments, include_args",
    [
        pytest.param({"extra_args": "extra_args"}, True),
        pytest.param(None, False),
    ],
)
async def test_open_ai_assistant_agent_invoke_stream(arguments, include_args):
    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAssistantAgent(client=client, definition=definition)
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


def test_open_ai_assistant_agent_get_channel_keys():
    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAssistantAgent(client=client, definition=definition)
    keys = list(agent.get_channel_keys())
    assert len(keys) >= 3


@pytest.fixture
def mock_thread():
    class MockThread:
        id = "test_thread_id"

    return MockThread()


async def test_open_ai_assistant_agent_create_channel(mock_thread):
    from semantic_kernel.agents.channels.open_ai_assistant_channel import OpenAIAssistantChannel

    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"
    agent = AzureAssistantAgent(client=client, definition=definition)
    client.beta = MagicMock()
    client.beta.assistants = MagicMock()
    client.beta.assistants.create = AsyncMock(return_value=definition)
    client.beta.threads = MagicMock()
    client.beta.threads.create = AsyncMock(return_value=mock_thread)
    ch = await agent.create_channel()
    assert isinstance(ch, OpenAIAssistantChannel)
    assert ch.thread_id == "test_thread_id"


def test_create_openai_client(azure_openai_unit_test_env):
    client, model = AzureAssistantAgent.setup_resources(api_key="test_api_key", default_headers={"user_agent": "test"})
    assert client is not None
    assert client.api_key == "test_api_key"
    assert model is not None


def test_create_azure_openai_client(azure_openai_unit_test_env):
    client, model = AzureAssistantAgent.setup_resources(
        api_key="test_api_key", endpoint="https://test_endpoint.com", default_headers={"user_agent": "test"}
    )
    assert model is not None
    assert client is not None
    assert client.api_key == "test_api_key"
    assert str(client.base_url) == "https://test_endpoint.com/openai/"


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT"]], indirect=True)
async def test_retrieve_agent_missing_endpoint_throws(kernel, azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="Please provide an Azure OpenAI endpoint"):
        _, _ = AzureAssistantAgent.setup_resources(
            env_file_path="./", api_key="test_api_key", default_headers={"user_agent": "test"}
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
async def test_retrieve_agent_missing_chat_deployment_name_throws(kernel, azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="Please provide an Azure OpenAI deployment name"):
        _, _ = AzureAssistantAgent.setup_resources(
            env_file_path="./",
            api_key="test_api_key",
            endpoint="https://test_endpoint.com",
            default_headers={"user_agent": "test"},
        )
