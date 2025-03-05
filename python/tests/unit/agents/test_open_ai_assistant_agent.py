# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from openai import AsyncOpenAI
from openai.resources.beta.assistants import Assistant
from openai.types.beta.assistant import (
    ToolResources,
    ToolResourcesCodeInterpreter,
    ToolResourcesFileSearch,
)
from pydantic import ValidationError

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_base import OpenAIAssistantBase
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException
from semantic_kernel.kernel import Kernel


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def mock_assistant_json():
    return Assistant(
        created_at=123456789,
        object="assistant",
        metadata={
            "__run_options": json.dumps({
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            })
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
        AgentInitializationException,
        match="Please provide an OpenAI api_key",
    ):
        OpenAIAssistantAgent._create_client(None)


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


async def test_create_agent_with_files(kernel: Kernel, openai_unit_test_env):
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
        patch.object(OpenAIAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant,
    ):
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel,
            ai_model_id="test_model_id",
            service_id="test_service",
            name="test_name",
            api_key="test_api_key",
            code_interpreter_filenames=["file1", "file2"],
            vector_store_filenames=["file3", "file4"],
            enable_code_interpreter=True,
            enable_file_search=True,
        )
        assert agent.assistant is not None
        mock_create_assistant.assert_called_once()


async def test_create_agent_with_code_files_not_found_raises_exception(kernel: Kernel, openai_unit_test_env):
    mock_open_file = mock_open(read_data="file_content")
    with (
        patch("builtins.open", mock_open_file),
        patch(
            "semantic_kernel.agents.open_ai.open_ai_assistant_base.OpenAIAssistantBase.add_file",
            side_effect=FileNotFoundError("File not found"),
        ),
        patch.object(OpenAIAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant,
    ):
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        with pytest.raises(AgentInitializationException, match="Failed to upload code interpreter files."):
            _ = await OpenAIAssistantAgent.create(
                kernel=kernel,
                service_id="test_service",
                ai_model_id="test_model_id",
                name="test_name",
                api_key="test_api_key",
                api_version="2024-05-01",
                code_interpreter_filenames=["file1", "file2"],
            )


async def test_create_agent_with_search_files_not_found_raises_exception(kernel: Kernel, openai_unit_test_env):
    mock_open_file = mock_open(read_data="file_content")
    with (
        patch("builtins.open", mock_open_file),
        patch(
            "semantic_kernel.agents.open_ai.open_ai_assistant_base.OpenAIAssistantBase.add_file",
            side_effect=FileNotFoundError("File not found"),
        ),
        patch.object(OpenAIAssistantAgent, "create_assistant", new_callable=AsyncMock) as mock_create_assistant,
    ):
        mock_create_assistant.return_value = MagicMock(spec=Assistant)
        with pytest.raises(AgentInitializationException, match="Failed to upload vector store files."):
            _ = await OpenAIAssistantAgent.create(
                kernel=kernel,
                service_id="test_service",
                ai_model_id="test_model_id",
                name="test_name",
                api_key="test_api_key",
                api_version="2024-05-01",
                vector_store_filenames=["file3", "file4"],
            )


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


async def test_list_definitions(kernel: Kernel, openai_unit_test_env):
    agent = OpenAIAssistantAgent(
        kernel=kernel, service_id="test_service", name="test_name", instructions="test_instructions", id="test_id"
    )

    assistant = Assistant(
        id="test_id",
        created_at=123456789,
        description="test_description",
        instructions="test_instructions",
        metadata={
            "__run_options": {
                "max_completion_tokens": 100,
                "max_prompt_tokens": 50,
                "parallel_tool_calls_enabled": True,
                "truncation_message_count": 10,
            }
        },
        model="test_model",
        name="test_name",
        object="assistant",
        temperature=0.7,
        tool_resources=ToolResources(
            code_interpreter=ToolResourcesCodeInterpreter(code_interpreter_file_ids=["file1", "file2"]),
            file_search=ToolResourcesFileSearch(vector_store_ids=["vector_store1"]),
        ),
        top_p=0.9,
        response_format={"type": "json_object"},
        tools=[{"type": "code_interpreter"}, {"type": "file_search"}],
    )

    with patch.object(
        OpenAIAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncOpenAI)
    ) as mock_create_client:
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()
        mock_client_instance.beta.assistants.list = AsyncMock(return_value=MagicMock(data=[assistant]))

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


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
async def test_retrieve_agent_missing_chat_model_id_throws(kernel, openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The OpenAI chat model ID is required."):
        _ = await OpenAIAssistantAgent.retrieve(
            id="test_id", api_key="test_api_key", kernel=kernel, env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
async def test_retrieve_agent_missing_api_key_throws(kernel, openai_unit_test_env):
    with pytest.raises(
        AgentInitializationException, match="The OpenAI API key is required, if a client is not provided."
    ):
        _ = await OpenAIAssistantAgent.retrieve(id="test_id", kernel=kernel, env_file_path="test.env")


def test_open_ai_settings_create_throws(openai_unit_test_env):
    with patch("semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings.OpenAISettings.create") as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationException, match="Failed to create OpenAI settings."):
            OpenAIAssistantAgent(
                service_id="test", api_key="test_api_key", org_id="test_org_id", ai_model_id="test_model_id"
            )


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
def test_azure_openai_agent_create_missing_chat_model_id_throws(openai_unit_test_env):
    with pytest.raises(AgentInitializationException, match="The OpenAI chat model ID is required."):
        OpenAIAssistantAgent(service_id="test_service", env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_azure_openai_agent_create_missing_api_key_throws(openai_unit_test_env):
    with pytest.raises(
        AgentInitializationException, match="The OpenAI API key is required, if a client is not provided."
    ):
        OpenAIAssistantAgent(env_file_path="test.env")


def test_create_open_ai_assistant_definition_with_json_metadata(mock_assistant_json, openai_unit_test_env):
    with (
        patch.object(
            OpenAIAssistantBase,
            "_create_open_ai_assistant_definition",
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
            },
        ) as mock_create_def,
    ):
        assert mock_create_def.return_value == {
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


async def test_retrieve_agent(kernel, openai_unit_test_env):
    with (
        patch.object(
            OpenAIAssistantAgent, "_create_client", return_value=MagicMock(spec=AsyncOpenAI)
        ) as mock_create_client,
        patch.object(
            OpenAIAssistantBase,
            "_create_open_ai_assistant_definition",
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
            },
        ) as mock_create_def,
    ):
        mock_client_instance = mock_create_client.return_value
        mock_client_instance.beta = MagicMock()
        mock_client_instance.beta.assistants = MagicMock()

        mock_client_instance.beta.assistants.retrieve = AsyncMock(return_value=AsyncMock(spec=Assistant))

        retrieved_agent = await OpenAIAssistantAgent.retrieve(id="test_id", api_key="test_api_key", kernel=kernel)
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
        mock_create_def.assert_called_once()


@pytest.mark.parametrize(
    "exclude_list, client, api_key, should_raise, expected_exception_msg, should_create_client_call",
    [
        ([], None, "test_api_key", False, None, True),
        ([], AsyncMock(spec=AsyncOpenAI), None, False, None, False),
        ([], AsyncMock(spec=AsyncOpenAI), "test_api_key", False, None, False),
        (
            ["OPENAI_API_KEY"],
            None,
            None,
            True,
            "The OpenAI API key is required, if a client is not provided.",
            False,
        ),
    ],
    indirect=["exclude_list"],
)
async def test_retrieve_agent_handling_api_key_and_client(
    openai_unit_test_env,
    exclude_list,
    kernel,
    client,
    api_key,
    should_raise,
    expected_exception_msg,
    should_create_client_call,
):
    is_api_key_present = "OPENAI_API_KEY" not in exclude_list

    with (
        patch.object(
            OpenAIAssistantAgent,
            "_create_open_ai_settings",
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
            OpenAIAssistantAgent,
            "_create_client",
            return_value=AsyncMock(spec=AsyncOpenAI),
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
                await OpenAIAssistantAgent.retrieve(id="test_id", kernel=kernel, api_key=api_key, client=client)
            return

        retrieved_agent = await OpenAIAssistantAgent.retrieve(
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
