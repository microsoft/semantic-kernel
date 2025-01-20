# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.beta.assistants import Assistant
from openai.types.beta.assistant import ToolResources, ToolResourcesCodeInterpreter, ToolResourcesFileSearch
from pydantic import ValidationError

from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException
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
            code_interpreter=ToolResourcesCodeInterpreter(code_interpreter_file_ids=["file1", "file2"]),
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
        AgentInitializationException,
        match="Please provide either AzureOpenAI api_key, an ad_token, ad_token_provider, or a client.",
    ):
        AzureAssistantAgent._create_client(None)


def test_create_client_from_configuration_missing_endpoint():
    with pytest.raises(
        AgentInitializationException,
        match="Please provide an AzureOpenAI endpoint.",
    ):
        AzureAssistantAgent._create_client(api_key="test")


async def test_create_agent(kernel: Kernel, azure_openai_unit_test_env):
    with patch.object(AzureAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant:
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        agent = await AzureAssistantAgent.create(
            kernel=kernel, service_id="test_service", name="test_name", api_key="test_api_key", api_version="2024-05-01"
        )
        assert agent.assistant is not None
        mock_create_assistant.assert_called_once()
        await agent.client.close()


async def test_create_agent_with_files(kernel: Kernel, azure_openai_unit_test_env):
    mock_open_file = mock_open(read_data="file_content")
    with (
        patch("builtins.open", mock_open_file),
        patch(
            "semantic_kernel.agents.open_ai.open_ai_assistant_base.OpenAIAssistantBase.add_file",
            return_value="test_file_id",
        ),
        patch(
            "semantic_kernel.agents.open_ai.open_ai_assistant_base.OpenAIAssistantBase.create_vector_store",
            return_value="vector_store_id",
        ),
        patch.object(AzureAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant,
    ):
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        agent = await AzureAssistantAgent.create(
            kernel=kernel,
            service_id="test_service",
            name="test_name",
            api_key="test_api_key",
            api_version="2024-05-01",
            code_interpreter_filenames=["file1", "file2"],
            vector_store_filenames=["file3", "file4"],
            enable_code_interpreter=True,
            enable_file_search=True,
        )
        assert agent.assistant is not None
        mock_create_assistant.assert_called_once()


async def test_create_agent_with_code_files_not_found_raises_exception(kernel: Kernel, azure_openai_unit_test_env):
    mock_open_file = mock_open(read_data="file_content")
    with (
        patch("builtins.open", mock_open_file),
        patch(
            "semantic_kernel.agents.open_ai.open_ai_assistant_base.OpenAIAssistantBase.add_file",
            side_effect=FileNotFoundError("File not found"),
        ),
        patch.object(AzureAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant,
    ):
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        with pytest.raises(AgentInitializationException, match="Failed to upload code interpreter files."):
            _ = await AzureAssistantAgent.create(
                kernel=kernel,
                service_id="test_service",
                deployment_name="test_deployment_name",
                name="test_name",
                api_key="test_api_key",
                api_version="2024-05-01",
                code_interpreter_filenames=["file1", "file2"],
            )


async def test_create_agent_with_search_files_not_found_raises_exception(kernel: Kernel, azure_openai_unit_test_env):
    mock_open_file = mock_open(read_data="file_content")
    with (
        patch("builtins.open", mock_open_file),
        patch(
            "semantic_kernel.agents.open_ai.open_ai_assistant_base.OpenAIAssistantBase.add_file",
            side_effect=FileNotFoundError("File not found"),
        ),
        patch.object(AzureAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant,
    ):
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        with pytest.raises(AgentInitializationException, match="Failed to upload vector store files."):
            _ = await AzureAssistantAgent.create(
                kernel=kernel,
                service_id="test_service",
                deployment_name="test_deployment_name",
                name="test_name",
                api_key="test_api_key",
                api_version="2024-05-01",
                vector_store_filenames=["file3", "file4"],
            )


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
            "code_interpreter_file_ids": ["file1", "file2"],
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


async def test_retrieve_agent(kernel, azure_openai_unit_test_env):
    with patch.object(
        AzureAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncAzureOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()

        mock_client_instance.beta.assistants.retrieve = AsyncMock(return_value=AsyncMock(spec=Assistant))

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
                "code_interpreter_file_ids": ["file1", "file2"],
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
                "code_interpreter_file_ids",
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
            "code_interpreter_file_ids": ["file1", "file2"],
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
async def test_retrieve_agent_missing_chat_deployment_name_throws(kernel, azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The Azure OpenAI chat_deployment_name is required."):
        _ = await AzureAssistantAgent.retrieve(
            id="test_id", api_key="test_api_key", kernel=kernel, env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
async def test_retrieve_agent_missing_api_key_throws(kernel, azure_openai_unit_test_env):
    with pytest.raises(
        AgentInitializationException, match="Please provide either a client, an api_key, ad_token or ad_token_provider."
    ):
        _ = await AzureAssistantAgent.retrieve(id="test_id", kernel=kernel, env_file_path="test.env")


def test_open_ai_settings_create_throws(azure_openai_unit_test_env):
    with patch(
        "semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings.AzureOpenAISettings.create"
    ) as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationException, match="Failed to create Azure OpenAI settings."):
            AzureAssistantAgent(service_id="test", api_key="test_api_key", deployment_name="test_deployment_name")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_openai_agent_create_missing_deployment_name(azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The Azure OpenAI chat_deployment_name is required."):
        AzureAssistantAgent(
            service_id="test_service", api_key="test_key", endpoint="https://example.com", env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_openai_agent_create_missing_api_key(azure_openai_unit_test_env):
    with pytest.raises(
        AgentInitializationException, match="Please provide either a client, an api_key, ad_token or ad_token_provider."
    ):
        AzureAssistantAgent(service_id="test_service", endpoint="https://example.com", env_file_path="test.env")


async def test_setup_client_and_token_with_existing_client():
    """Test that if a client is already provided, _setup_client_and_token
    simply returns that client (and doesn't create a new one).
    """
    mock_settings = MagicMock()
    mock_settings.chat_deployment_name = "test_deployment_name"
    mock_settings.api_key = None
    mock_settings.token_endpoint = None
    mock_client = MagicMock(spec=AsyncAzureOpenAI)

    returned_client, returned_token = AzureAssistantAgent._setup_client_and_token(
        azure_openai_settings=mock_settings,
        ad_token=None,
        ad_token_provider=None,
        client=mock_client,
        default_headers=None,
    )

    assert returned_client == mock_client
    assert returned_token is None


async def test_setup_client_and_token_with_api_key_creates_client():
    """Test that providing an API key (and no client) results
    in creating a new client via _create_client.
    """
    mock_settings = MagicMock()
    mock_settings.chat_deployment_name = "test_deployment_name"
    mock_settings.api_key.get_secret_value.return_value = "test_api_key"
    mock_settings.endpoint = "https://test.endpoint"
    mock_settings.api_version = "2024-05-01"
    mock_settings.token_endpoint = None

    with patch.object(AzureAssistantAgent, "_create_client", return_value="mock_client") as mock_create_client:
        returned_client, returned_token = AzureAssistantAgent._setup_client_and_token(
            azure_openai_settings=mock_settings,
            ad_token=None,
            ad_token_provider=None,
            client=None,
            default_headers=None,
        )

        mock_create_client.assert_called_once_with(
            api_key="test_api_key",
            endpoint="https://test.endpoint",
            api_version="2024-05-01",
            ad_token=None,
            ad_token_provider=None,
            default_headers=None,
        )
        assert returned_client == "mock_client"
        assert returned_token is None


async def test_setup_client_and_token_fetches_ad_token_when_token_endpoint_present():
    """Test that if no credentials are provided except a token endpoint,
    _setup_client_and_token fetches an AD token.
    """
    mock_settings = MagicMock()
    mock_settings.chat_deployment_name = "test_deployment_name"
    mock_settings.api_key = None
    mock_settings.endpoint = "https://test.endpoint"
    mock_settings.api_version = "2024-05-01"
    mock_settings.token_endpoint = "https://login.microsoftonline.com"

    with (
        patch(
            "semantic_kernel.agents.open_ai.azure_assistant_agent.get_entra_auth_token",
            return_value="fetched_ad_token",
        ) as mock_get_token,
        patch.object(AzureAssistantAgent, "_create_client", return_value="mock_client") as mock_create_client,
    ):
        returned_client, returned_token = AzureAssistantAgent._setup_client_and_token(
            azure_openai_settings=mock_settings,
            ad_token=None,
            ad_token_provider=None,
            client=None,
            default_headers=None,
        )

        mock_get_token.assert_called_once_with("https://login.microsoftonline.com")
        mock_create_client.assert_called_once_with(
            api_key=None,
            endpoint="https://test.endpoint",
            api_version="2024-05-01",
            ad_token="fetched_ad_token",
            ad_token_provider=None,
            default_headers=None,
        )
        assert returned_client == "mock_client"
        assert returned_token == "fetched_ad_token"


async def test_setup_client_and_token_no_credentials_raises_exception():
    """Test that if there's no client, no API key, no AD token/provider,
    and no token endpoint, an AgentInitializationException is raised.
    """
    mock_settings = MagicMock()
    mock_settings.chat_deployment_name = "test_deployment_name"
    mock_settings.api_key = None
    mock_settings.endpoint = "https://test.endpoint"
    mock_settings.api_version = "2024-05-01"
    mock_settings.token_endpoint = None

    with pytest.raises(
        AgentInitializationException, match="Please provide either a client, an api_key, ad_token or ad_token_provider."
    ):
        _ = AzureAssistantAgent._setup_client_and_token(
            azure_openai_settings=mock_settings,
            ad_token=None,
            ad_token_provider=None,
            client=None,
            default_headers=None,
        )


@pytest.mark.parametrize(
    "exclude_list, client, api_key, should_raise, expected_exception_msg, should_create_client_call",
    [
        ([], None, "test_api_key", False, None, True),
        ([], AsyncMock(spec=AsyncAzureOpenAI), None, False, None, False),
        (
            [],
            AsyncMock(spec=AsyncAzureOpenAI),
            "test_api_key",
            False,
            None,
            False,
        ),
        (
            ["AZURE_OPENAI_API_KEY"],
            None,
            None,
            True,
            "Please provide either a client, an api_key, ad_token or ad_token_provider.",
            False,
        ),
    ],
    indirect=["exclude_list"],
)
async def test_retrieve_agent_handling_api_key_and_client(
    azure_openai_unit_test_env,
    exclude_list,
    kernel,
    client,
    api_key,
    should_raise,
    expected_exception_msg,
    should_create_client_call,
):
    is_api_key_present = "AZURE_OPENAI_API_KEY" not in exclude_list

    with (
        patch.object(
            AzureAssistantAgent,
            "_create_azure_openai_settings",
            return_value=MagicMock(
                chat_model_id="test_model",
                api_key=MagicMock(
                    get_secret_value=MagicMock(return_value="test_api_key" if is_api_key_present else None)
                )
                if is_api_key_present
                else None,
            ),
        ),
        patch.object(
            AzureAssistantAgent,
            "_create_client",
            return_value=AsyncMock(spec=AsyncAzureOpenAI),
        ) as mock_create_client,
        patch.object(
            OpenAIAssistantBase,
            "_create_open_ai_assistant_definition",
            return_value={
                "ai_model_id": "test_model",
                "description": "test_description",
                "id": "test_id",
                "name": "test_name",
            },
        ) as mock_create_def,
    ):
        if client:
            client.beta = MagicMock()
            client.beta.assistants = MagicMock()
            client.beta.assistants.retrieve = AsyncMock(return_value=MagicMock(spec=Assistant))
        else:
            mock_client_instance = mock_create_client.return_value
            mock_client_instance.beta = MagicMock()
            mock_client_instance.beta.assistants = MagicMock()
            mock_client_instance.beta.assistants.retrieve = AsyncMock(return_value=MagicMock(spec=Assistant))

        if should_raise:
            with pytest.raises(AgentInitializationException, match=expected_exception_msg):
                await AzureAssistantAgent.retrieve(id="test_id", kernel=kernel, api_key=api_key, client=client)
            return

        retrieved_agent = await AzureAssistantAgent.retrieve(
            id="test_id", kernel=kernel, api_key=api_key, client=client
        )

        if should_create_client_call:
            mock_create_client.assert_called_once()
        else:
            mock_create_client.assert_not_called()

        assert retrieved_agent.ai_model_id == "test_model"
        mock_create_def.assert_called_once()
        if client:
            client.beta.assistants.retrieve.assert_called_once_with("test_id")
        else:
            mock_client_instance.beta.assistants.retrieve.assert_called_once_with("test_id")
