# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, Mock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.completions import AsyncCompletions
from openai.types import Completion

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
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
    assert (
        azure_text_completion.ai_model_id
        == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
    )
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
    assert (
        azure_text_completion.ai_model_id
        == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]
    )
    assert isinstance(azure_text_completion, TextCompletionClientBase)
    for key, value in default_headers.items():
        assert key in azure_text_completion.client.default_headers
        assert azure_text_completion.client.default_headers[key] == value


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]], indirect=True
)
def test_init_with_empty_deployment_name(
    monkeypatch, azure_openai_unit_test_env
) -> None:
@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"]], indirect=True)
def test_init_with_empty_deployment_name(monkeypatch, azure_openai_unit_test_env) -> None:
def test_azure_text_completion_init_with_empty_deployment_name(monkeypatch, azure_openai_unit_test_env) -> None:
    monkeypatch.delenv("AZURE_OPENAI_TEXT_DEPLOYMENT_NAME", raising=False)
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True
)
@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}],
    indirect=True,
)
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
    mock_text_content,
    mock_metadata,
    mock_create,
    azure_openai_unit_test_env,
    mock_text_completion_response,
) -> None:
    mock_create.return_value = mock_text_completion_response
    prompt = "hello world"
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings()
    azure_text_completion = AzureTextCompletion()

    await azure_text_completion.get_text_contents(
        prompt=prompt, settings=complete_prompt_execution_settings
    )

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
    mock_text_content,
    mock_metadata,
    mock_create,
    azure_openai_unit_test_env,
    mock_text_completion_response,
) -> None:
    mock_create.return_value = mock_text_completion_response
    prompt = "hello world"
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings()

    token_bias = {"200": 100}
    complete_prompt_execution_settings.logit_bias = token_bias

    azure_text_completion = AzureTextCompletion()

    await azure_text_completion.get_text_contents(
        prompt=prompt, settings=complete_prompt_execution_settings
    )

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
        "deployment_name": azure_openai_unit_test_env[
            "AZURE_OPENAI_TEXT_DEPLOYMENT_NAME"
        ],
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
