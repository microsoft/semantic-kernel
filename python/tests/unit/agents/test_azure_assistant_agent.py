# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.beta.assistants import Assistant
from openai.types.beta.assistant import ToolResources, ToolResourcesCodeInterpreter, ToolResourcesFileSearch
from pydantic import ValidationError

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError
from semantic_kernel.kernel import Kernel


@pytest.fixture
def azure_openai_assistant_agent(kernel: Kernel, azure_openai_unit_test_env):
    return AzureAssistantAgent(
        kernel=kernel,
        service_id="test_service",
        name="test_name",
        instructions="test_instructions",
        api_key="test_api_key",
        endpoint="https://test.endpoint",
        ai_model_id="test_model",
        api_version="2024-05-01-preview",
        default_headers={"User-Agent": "test-agent"},
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


def test_initialization(azure_openai_assistant_agent: AzureAssistantAgent, azure_openai_unit_test_env):
    agent = azure_openai_assistant_agent
    assert agent is not None


def test_create_client(azure_openai_assistant_agent, azure_openai_unit_test_env):
    assert isinstance(azure_openai_assistant_agent.client, AsyncAzureOpenAI)


def test_create_client_from_configuration(azure_openai_assistant_agent, azure_openai_unit_test_env):
    assert isinstance(azure_openai_assistant_agent.client, AsyncAzureOpenAI)
    assert azure_openai_assistant_agent.client.api_key == "test_api_key"


def test_create_client_from_configuration_missing_api_key():
    with pytest.raises(
        AgentInitializationError,
        match="Please provide either AzureOpenAI api_key, an ad_token or an ad_token_provider or a client.",
    ):
        AzureAssistantAgent._create_client(None)


def test_create_client_from_configuration_missing_endpoint():
    with pytest.raises(
        AgentInitializationError,
        match="Please provide an AzureOpenAI endpoint.",
    ):
        AzureAssistantAgent._create_client(api_key="test")


@pytest.mark.asyncio
async def test_create_agent(kernel: Kernel, azure_openai_unit_test_env):
    with patch.object(AzureAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant:
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        agent = await AzureAssistantAgent.create(
            kernel=kernel, service_id="test_service", name="test_name", api_key="test_api_key", api_version="2024-05-01"
        )
        assert agent.assistant is not None
        mock_create_assistant.assert_called_once()
        await agent.client.close()


@pytest.mark.asyncio
async def test_list_definitions(kernel: Kernel, mock_assistant, azure_openai_unit_test_env):
    agent = AzureAssistantAgent(
        kernel=kernel, service_id="test_service", name="test_name", instructions="test_instructions", id="test_id"
    )

    with patch.object(
        AzureAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncAzureOpenAI)
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
async def test_retrieve_agent(kernel, azure_openai_unit_test_env):
    with patch.object(
        AzureAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncAzureOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()

        mock_client_instance.beta.assistants.retrieve = AsyncMock(return_value=AsyncMock())

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

        retrieved_agent = await AzureAssistantAgent.retrieve(id="test_id", api_key="test_api_key", kernel=kernel)
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


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
@pytest.mark.asyncio
async def test_retrieve_agent_missing_chat_deployment_name_throws(kernel, azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The Azure OpenAI chat_deployment_name is required."):
        _ = await AzureAssistantAgent.retrieve(
            id="test_id", api_key="test_api_key", kernel=kernel, env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
@pytest.mark.asyncio
async def test_retrieve_agent_missing_api_key_throws(kernel, azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="Please provide either api_key, ad_token or ad_token_provider."):
        _ = await AzureAssistantAgent.retrieve(id="test_id", kernel=kernel, env_file_path="test.env")


def test_open_ai_settings_create_throws(azure_openai_unit_test_env):
    with patch(
        "semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings.AzureOpenAISettings.create"
    ) as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationError, match="Failed to create Azure OpenAI settings."):
            AzureAssistantAgent(service_id="test", api_key="test_api_key", deployment_name="test_deployment_name")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_openai_agent_create_missing_deployment_name(azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The Azure OpenAI chat_deployment_name is required."):
        AzureAssistantAgent(
            service_id="test_service", api_key="test_key", endpoint="https://example.com", env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_openai_agent_create_missing_api_key(azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="Please provide either api_key, ad_token or ad_token_provider."):
        AzureAssistantAgent(service_id="test_service", endpoint="https://example.com", env_file_path="test.env")
