# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, Mock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.completions import AsyncCompletions
from openai.types import Completion

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import AzureTextCompletion
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import AzureTextCompletion
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import AzureTextCompletion
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ServiceInitializationError


@pytest.fixture
def mock_text_completion_response() -> Mock:
    mock_response = Mock(spec=Completion)
    mock_response.id = "test_id"
    mock_response.created = "time"
    mock_response.usage = None
    mock_response.choices = []
    return mock_response


def test_init(azure_openai_unit_test_env) -> None:
    # Test successful initialization
    azure_text_completion = AzureTextCompletion()

    assert azure_text_completion.client is not None
    assert isinstance(azure_text_completion.client, AsyncAzureOpenAI)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    assert (
        azure_text_completion.ai_model_id
        == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    assert isinstance(azure_text_completion, TextCompletionClientBase)


def test_init_with_custom_header(azure_openai_unit_test_env) -> None:
    # Custom header for testing
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    azure_text_completion = AzureTextCompletion(
        default_headers=default_headers,
    )

    assert azure_text_completion.client is not None
    assert isinstance(azure_text_completion.client, AsyncAzureOpenAI)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    assert (
        azure_text_completion.ai_model_id
        == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======
    assert azure_text_completion.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    assert isinstance(azure_text_completion, TextCompletionClientBase)
    for key, value in default_headers.items():
        assert key in azure_text_completion.client.default_headers
        assert azure_text_completion.client.default_headers[key] == value


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@pytest.mark.parametrize(
    "exclude_list", [["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]], indirect=True
)
def test_init_with_empty_deployment_name(
    monkeypatch, azure_openai_unit_test_env
) -> None:
@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]], indirect=True)
def test_init_with_empty_deployment_name(monkeypatch, azure_openai_unit_test_env) -> None:
def test_azure_text_completion_init_with_empty_deployment_name(monkeypatch, azure_openai_unit_test_env) -> None:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
def test_azure_text_embedding_generates_no_token_with_api_key_in_env(azure_openai_unit_test_env) -> None:
    with (
        patch(
            f"{AzureOpenAISettings.__module__}.{AzureOpenAISettings.__qualname__}.get_azure_openai_auth_token",
        ) as mock_get_token,
    ):
        mock_get_token.return_value = "test_token"
        azure_text_completion = AzureTextCompletion()

        assert azure_text_completion.client is not None
        # API key is provided in env var, so the ad_token should be None
        assert mock_get_token.call_count == 0


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]], indirect=True)
def test_init_with_empty_deployment_name(monkeypatch, azure_openai_unit_test_env) -> None:
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    monkeypatch.delenv("AZURE_OPENAI_TEXT_DEPLOYMENT_NAME", raising=False)
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion(
            env_file_path="test.env",
        )


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True
)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion(
            env_file_path="test.env",
        )


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}],
    indirect=True,
)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
def test_init_with_invalid_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion()


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.azure_text_completion.AzureTextCompletion._get_metadata_from_text_response",
    return_value={"test": "test"},
)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.azure_text_completion.AzureTextCompletion._create_text_content",
    return_value=Mock(spec=TextContent),
)
async def test_call_with_parameters(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    mock_text_content,
    mock_metadata,
    mock_create,
    azure_openai_unit_test_env,
    mock_text_completion_response,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
) -> None:
    mock_create.return_value = mock_text_completion_response
    prompt = "hello world"
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings()
    azure_text_completion = AzureTextCompletion()

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    await azure_text_completion.get_text_contents(
        prompt=prompt, settings=complete_prompt_execution_settings
    )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    await azure_text_completion.get_text_contents(
        prompt=prompt, settings=complete_prompt_execution_settings
    )
=======
    await azure_text_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    await azure_text_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    await azure_text_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"],
        stream=False,
        prompt=prompt,
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.azure_text_completion.AzureTextCompletion._get_metadata_from_text_response",
    return_value={"test": "test"},
)
@patch(
    "semantic_kernel.connectors.ai.open_ai.services.azure_text_completion.AzureTextCompletion._create_text_content",
    return_value=Mock(spec=TextContent),
)
async def test_call_with_parameters_logit_bias_not_none(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    mock_text_content,
    mock_metadata,
    mock_create,
    azure_openai_unit_test_env,
    mock_text_completion_response,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    mock_text_content, mock_metadata, mock_create, azure_openai_unit_test_env, mock_text_completion_response
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
) -> None:
    mock_create.return_value = mock_text_completion_response
    prompt = "hello world"
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings()

    token_bias = {"200": 100}
    complete_prompt_execution_settings.logit_bias = token_bias

    azure_text_completion = AzureTextCompletion()

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    await azure_text_completion.get_text_contents(
        prompt=prompt, settings=complete_prompt_execution_settings
    )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    await azure_text_completion.get_text_contents(
        prompt=prompt, settings=complete_prompt_execution_settings
    )
=======
    await azure_text_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    await azure_text_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    await azure_text_completion.get_text_contents(prompt=prompt, settings=complete_prompt_execution_settings)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

    mock_create.assert_awaited_once_with(
        model=azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"],
        logit_bias=complete_prompt_execution_settings.logit_bias,
        stream=False,
        prompt=prompt,
        echo=False,
    )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_serialize(azure_openai_unit_test_env) -> None:
    default_headers = {"X-Test": "test"}

    settings = {
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        "deployment_name": azure_openai_unit_test_env[
            "AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"
        ],
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        "deployment_name": azure_openai_unit_test_env[
            "AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"
        ],
=======
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"],
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"],
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"],
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        "endpoint": azure_openai_unit_test_env["AZURE_OPENAI_ENDPOINT"],
        "api_key": azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"],
        "api_version": azure_openai_unit_test_env["AZURE_OPENAI_API_VERSION"],
        "default_headers": default_headers,
    }

    azure_text_completion = AzureTextCompletion.from_dict(settings)
    dumped_settings = azure_text_completion.to_dict()
    assert dumped_settings["ai_model_id"] == settings["deployment_name"]
    assert settings["endpoint"] in str(dumped_settings["base_url"])
    assert settings["deployment_name"] in str(dumped_settings["base_url"])
    assert settings["api_key"] == dumped_settings["api_key"]
    assert settings["api_version"] == dumped_settings["api_version"]

    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value
