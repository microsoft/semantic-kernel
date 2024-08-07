# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant
from openai.types.beta.assistant import (
    ToolResources,
    ToolResourcesCodeInterpreter,
    ToolResourcesFileSearch,
)
from pydantic import ValidationError

from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError
from semantic_kernel.kernel import Kernel


@pytest.fixture
def openai_assistant_agent(kernel: Kernel, openai_unit_test_env):
    return OpenAIAssistantAgent(
        kernel=kernel,
        service_id="test_service",
        name="test_name",
        instructions="test_instructions",
        api_key="test_api_key",
        kwargs={"temperature": 0.1},
        max_completion_tokens=100,
        max_prompt_tokens=100,
        parallel_tool_calls_enabled=True,
        truncation_message_count=2,
    )


@pytest.fixture
def mock_assistant():
    return Assistant(
        created_at=123456789,
        object="assistant",
        metadata={
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        },
        model="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
        temperature=0.7,
        top_p=0.9,
        response_format={"type": "json_object"},
        tool_resources=ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        ),
    )


@pytest.fixture
def mock_assistant_json():
    return Assistant(
        created_at=123456789,
        object="assistant",
        metadata={
            "__run_options": json.dumps(
                {
                    "max_completion_tokens": 100,
                    "max_prompt_tokens": 50,
                    "parallel_tool_calls_enabled": True,
                    "truncation_message_count": 10,
                }
            )
        },
        model="test_model",
        description="test_description",
        id="test_id",
        instructions="test_instructions",
        name="test_name",
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
        temperature=0.7,
        top_p=0.9,
        response_format={"type": "json_object"},
        tool_resources=ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        ),
    )


def test_initialization(openai_assistant_agent: OpenAIAssistantAgent, openai_unit_test_env):
    agent = openai_assistant_agent
    assert agent is not None
    agent.kernel is not None


def test_create_client(openai_unit_test_env):
    client = OpenAIAssistantAgent._create_client(api_key="test_api_key", default_headers={"User-Agent": "test-agent"})
    assert isinstance(client, AsyncOpenAI)
    assert client.api_key == "test_api_key"


def test_create_client_from_configuration_missing_api_key():
    with pytest.raises(
        AgentInitializationError,
        match="Please provide an OpenAI api_key",
    ):
        OpenAIAssistantAgent._create_client(None)


@pytest.mark.asyncio
async def test_create_agent(kernel: Kernel, openai_unit_test_env):
    with patch.object(OpenAIAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant:
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel,
            ai_model_id="test_model_id",
            service_id="test_service",
            name="test_name",
            api_key="test_api_key",
        )
        assert agent.assistant is not None
        mock_create_assistant.assert_called_once()


@pytest.mark.asyncio
async def test_create_agent_second_way(kernel: Kernel, mock_assistant, openai_unit_test_env):
    agent = OpenAIAssistantAgent(
        kernel=kernel,
        ai_model_id="test_model_id",
        service_id="test_service",
        name="test_name",
        api_key="test_api_key",
        max_completion_tokens=100,
        max_prompt_tokens=100,
        parallel_tool_calls_enabled=True,
        truncation_message_count=2,
    )

    with patch.object(
        OpenAIAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants.create = AsyncMock(return_value=mock_assistant)

        agent.client = mock_client_instance

        assistant = await agent.create_assistant()

        mock_client_instance.beta.assistants.create.assert_called_once()

        assert assistant == mock_assistant

        assert json.loads(
            mock_client_instance.beta.assistants.create.call_args[1]["metadata"][agent._options_metadata_key]
        ) == {
            "max_completion_tokens": 100,
            "max_prompt_tokens": 100,
            "parallel_tool_calls_enabled": True,
            "truncation_message_count": 2,
        }


@pytest.mark.asyncio
async def test_list_definitions(kernel: Kernel, mock_assistant, openai_unit_test_env):
    agent = OpenAIAssistantAgent(
        kernel=kernel, service_id="test_service", name="test_name", instructions="test_instructions", id="test_id"
    )

    with patch.object(
        OpenAIAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()
        mock_client_instance.beta.assistants.list = AsyncMock(return_value=MagicMock(data=[mock_assistant]))

        agent.client = mock_client_instance

        definitions = []
        async for definition in agent.list_definitions():
            definitions.append(definition)

        mock_client_instance.beta.assistants.list.assert_called()

        assert len(definitions) == 1
        assert definitions[0] == {
            "ai_model_id": "test_model",
            "description": "test_description",
            "id": "test_id",
            "instructions": "test_instructions",
            "name": "test_name",
            "enable_code_interpreter": True,
            "enable_file_search": True,
            "enable_json_response": True,
            "file_ids": ["file1", "file2"],
            "temperature": 0.7,
            "top_p": 0.9,
            "vector_store_id": "vector_store1",
            "metadata": {
                "__run_options": {
                    "max_completion_tokens": 100,
                    "max_prompt_tokens": 50,
                    "parallel_tool_calls_enabled": True,
                    "truncation_message_count": 10,
                }
            },
            "max_completion_tokens": 100,
            "max_prompt_tokens": 50,
            "parallel_tool_calls_enabled": True,
            "truncation_message_count": 10,
        }


@pytest.mark.asyncio
async def test_retrieve_agent(kernel, openai_unit_test_env):
    with patch.object(
        OpenAIAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()

        mock_client_instance.beta.assistants.retrieve = AsyncMock(return_value=AsyncMock())

        agent = OpenAIAssistantAgent(
            kernel=kernel, service_id="test_service", name="test_name", instructions="test_instructions", id="test_id"
        )
        OpenAIAssistantBase._create_open_ai_assistant_definition = MagicMock(
            return_value={
                "ai_model_id": "test_model",
                "description": "test_description",
                "id": "test_id",
                "instructions": "test_instructions",
                "name": "test_name",
                "enable_code_interpreter": True,
                "enable_file_search": True,
                "enable_json_response": True,
                "file_ids": ["file1", "file2"],
                "temperature": 0.7,
                "top_p": 0.9,
                "vector_store_id": "vector_store1",
                "metadata": {
                    "__run_options": {
                        "max_completion_tokens": 100,
                        "max_prompt_tokens": 50,
                        "parallel_tool_calls_enabled": True,
                        "truncation_message_count": 10,
                    }
                },
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        )

        retrieved_agent = await agent.retrieve(id="test_id", api_key="test_api_key", kernel=kernel)
        assert retrieved_agent.model_dump(
            include={
                "ai_model_id",
                "description",
                "id",
                "instructions",
                "name",
                "enable_code_interpreter",
                "enable_file_search",
                "enable_json_response",
                "file_ids",
                "temperature",
                "top_p",
                "vector_store_id",
                "metadata",
                "max_completion_tokens",
                "max_prompt_tokens",
                "parallel_tool_calls_enabled",
                "truncation_message_count",
            }
        ) == {
            "ai_model_id": "test_model",
            "description": "test_description",
            "id": "test_id",
            "instructions": "test_instructions",
            "name": "test_name",
            "enable_code_interpreter": True,
            "enable_file_search": True,
            "enable_json_response": True,
            "file_ids": ["file1", "file2"],
            "temperature": 0.7,
            "top_p": 0.9,
            "vector_store_id": "vector_store1",
            "metadata": {
                "__run_options": {
                    "max_completion_tokens": 100,
                    "max_prompt_tokens": 50,
                    "parallel_tool_calls_enabled": True,
                    "truncation_message_count": 10,
                }
            },
            "max_completion_tokens": 100,
            "max_prompt_tokens": 50,
            "parallel_tool_calls_enabled": True,
            "truncation_message_count": 10,
        }
        mock_client_instance.beta.assistants.retrieve.assert_called_once_with("test_id")
        OpenAIAssistantBase._create_open_ai_assistant_definition.assert_called_once()


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
@pytest.mark.asyncio
async def test_retrieve_agent_missing_chat_model_id_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The OpenAI chat model ID is required."):
        _ = await OpenAIAssistantAgent.retrieve(
            id="test_id", api_key="test_api_key", kernel=kernel, env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
@pytest.mark.asyncio
async def test_retrieve_agent_missing_api_key_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The OpenAI API key is required, if a client is not provided."):
        _ = await OpenAIAssistantAgent.retrieve(id="test_id", kernel=kernel, env_file_path="test.env")


def test_open_ai_settings_create_throws(openai_unit_test_env):
    with patch("semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings.OpenAISettings.create") as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationError, match="Failed to create OpenAI settings."):
            OpenAIAssistantAgent(
                service_id="test", api_key="test_api_key", org_id="test_org_id", ai_model_id="test_model_id"
            )


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
def test_azure_openai_agent_create_missing_chat_model_id_throws(openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The OpenAI chat model ID is required."):
        OpenAIAssistantAgent(service_id="test_service", env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_azure_openai_agent_create_missing_api_key_throws(openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The OpenAI API key is required, if a client is not provided."):
        OpenAIAssistantAgent(env_file_path="test.env")


def test_create_open_ai_assistant_definition(mock_assistant, openai_unit_test_env):
    agent = OpenAIAssistantAgent(
        kernel=None, service_id="test_service", name="test_name", instructions="test_instructions", id="test_id"
    )

    definition = agent._create_open_ai_assistant_definition(mock_assistant)

    assert definition == {
        "ai_model_id": "test_model",
        "description": "test_description",
        "id": "test_id",
        "instructions": "test_instructions",
        "name": "test_name",
        "enable_code_interpreter": True,
        "enable_file_search": True,
        "enable_json_response": True,
        "file_ids": ["file1", "file2"],
        "temperature": 0.7,
        "top_p": 0.9,
        "vector_store_id": "vector_store1",
        "metadata": {
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        },
        "max_completion_tokens": 100,
        "max_prompt_tokens": 50,
        "parallel_tool_calls_enabled": True,
        "truncation_message_count": 10,
    }


def test_create_open_ai_assistant_definition_with_json_metadata(mock_assistant_json, openai_unit_test_env):
    agent = OpenAIAssistantAgent(
        kernel=None, service_id="test_service", name="test_name", instructions="test_instructions", id="test_id"
    )

    definition = agent._create_open_ai_assistant_definition(mock_assistant_json)

    assert definition == {
        "ai_model_id": "test_model",
        "description": "test_description",
        "id": "test_id",
        "instructions": "test_instructions",
        "name": "test_name",
        "enable_code_interpreter": True,
        "enable_file_search": True,
        "enable_json_response": True,
        "file_ids": ["file1", "file2"],
        "temperature": 0.7,
        "top_p": 0.9,
        "vector_store_id": "vector_store1",
        "metadata": {
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        },
        "max_completion_tokens": 100,
        "max_prompt_tokens": 50,
        "parallel_tool_calls_enabled": True,
        "truncation_message_count": 10,
    }
