# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant

from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.open_ai.open_ai_service_configuration import OpenAIServiceConfiguration
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError


@pytest.fixture
def configuration():
    return OpenAIServiceConfiguration(
        ai_model_id="test_model",
        service_id="test_service",
        api_key="test_api_key",
        default_headers={"User-Agent": "test-agent"},
    )


@pytest.fixture
def definition():
    return OpenAIAssistantDefinition(
        ai_model_id="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        enable_code_interpreter=True,
        enable_file_search=True,
        enable_json_response=True,
        file_ids=["file1", "file2"],
        temperature=0.7,
        top_p=0.9,
        vector_store_ids=["vector_store1"],
        metadata={"key": "value"},
        execution_settings=None,
    )


def test_initialization(configuration, definition, kernel):
    agent = OpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)
    assert agent.kernel == kernel
    assert agent.configuration == configuration
    assert agent.definition == definition


def test_create_client(configuration):
    client = OpenAIAssistantAgent.create_client(configuration=configuration)
    assert isinstance(client, AsyncOpenAI)


def test_create_client_from_configuration(configuration):
    client = OpenAIAssistantAgent._create_client_from_configuration(configuration)
    assert isinstance(client, AsyncOpenAI)
    assert client.api_key == "test_api_key"


def test_create_client_from_configuration_missing_api_key():
    config = OpenAIServiceConfiguration(
        service_id="test_service",
        ai_model_id="test_model",
    )
    with pytest.raises(
        AgentInitializationError,
        match="Please provide an OpenAI api_key",
    ):
        OpenAIAssistantAgent._create_client_from_configuration(config)


@pytest.mark.asyncio
async def test_create_agent(kernel, configuration, definition):
    with patch.object(OpenAIAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant:
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        agent = await OpenAIAssistantAgent.create(kernel=kernel, configuration=configuration, definition=definition)
        assert agent.assistant is not None
        mock_create_assistant.assert_called_once()


@pytest.mark.asyncio
async def test_list_definitions(configuration, kernel):
    definition = MagicMock(spec=OpenAIAssistantDefinition)
    definition.ai_model_id = "test_model"
    definition.description = "test_description"
    definition.id = "test_id"
    definition.instructions = "test_instructions"
    definition.name = "test_name"

    agent = OpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    with patch.object(
        OpenAIAssistantAgent, "_create_client_from_configuration", return_value=MagicMock(spec=AsyncOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()
        mock_assistant = MagicMock()
        mock_assistant.metadata = {
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        }
        mock_assistant.model = "test_model"
        mock_assistant.description = "test_description"
        mock_assistant.id = "test_id"
        mock_assistant.instructions = "test_instructions"
        mock_assistant.name = "test_name"
        mock_assistant.tools = ["code_interpreter", "file_search"]
        mock_assistant.temperature = 0.7
        mock_assistant.top_p = 0.9
        mock_assistant.response_format = {"type": "json_object"}
        mock_assistant.tool_resources = {
            "code_interpreter": {"file_ids": ["file1", "file2"]},
            "file_search": {"vector_store_ids": ["vector_store1"]},
        }
        mock_client_instance.beta.assistants.list = AsyncMock(return_value=MagicMock(data=[mock_assistant]))

        async for _ in agent.list_definitions(configuration):
            pass

        mock_client_instance.beta.assistants.list.assert_called_once_with(order="desc")


@pytest.mark.asyncio
async def test_retrieve_agent(kernel, configuration, definition):
    with patch.object(
        OpenAIAssistantAgent, "_create_client_from_configuration", return_value=MagicMock(spec=AsyncOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()
        mock_client_instance.beta.assistants.retrieve = AsyncMock(return_value=MagicMock())

        agent = OpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)
        agent._create_open_ai_assistant_definition = MagicMock(return_value=definition)

        retrieved_agent = await agent.retrieve(kernel, configuration, "test_id")
        assert retrieved_agent.definition == definition
        mock_client_instance.beta.assistants.retrieve.assert_called_once_with("test_id")
