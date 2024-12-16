# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import httpx
import pytest
from openai import AsyncAzureOpenAI, _legacy_response
from openai.resources.audio.speech import AsyncSpeech

from semantic_kernel.connectors.ai.open_ai import AzureTextToAudio
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_azure_text_to_audio_init(azure_openai_unit_test_env) -> None:
    azure_text_to_audio = AzureTextToAudio()

    assert azure_text_to_audio.client is not None
    assert isinstance(azure_text_to_audio.client, AsyncAzureOpenAI)
    assert azure_text_to_audio.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME"]


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_text_to_audio_init_with_empty_deployment_name(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="The Azure OpenAI text to audio deployment name is required."):
        AzureTextToAudio(env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_text_to_audio_init_with_empty_api_key(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextToAudio(env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_azure_text_to_audio_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="Please provide an endpoint or a base_url"):
        AzureTextToAudio(env_file_path="test.env")


@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
def test_azure_text_to_audio_init_with_invalid_http_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="Invalid settings: "):
        AzureTextToAudio()


@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"AZURE_OPENAI_BASE_URL": "https://test_text_to_audio_deployment.test-base-url.com"}],
    indirect=True,
)
def test_azure_text_to_audio_init_with_from_dict(azure_openai_unit_test_env) -> None:
    default_headers = {"test_header": "test_value"}

    settings = {
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME"],
        "endpoint": azure_openai_unit_test_env["AZURE_OPENAI_ENDPOINT"],
        "api_key": azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"],
        "api_version": azure_openai_unit_test_env["AZURE_OPENAI_API_VERSION"],
        "default_headers": default_headers,
    }

    azure_text_to_audio = AzureTextToAudio.from_dict(settings=settings)

    assert azure_text_to_audio.client is not None
    assert isinstance(azure_text_to_audio.client, AsyncAzureOpenAI)
    assert azure_text_to_audio.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME"]
    assert settings["deployment_name"] in str(azure_text_to_audio.client.base_url)
    assert azure_text_to_audio.client.api_key == azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"]

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in azure_text_to_audio.client.default_headers
        assert azure_text_to_audio.client.default_headers[key] == value


@patch.object(AsyncSpeech, "create", return_value=_legacy_response.HttpxBinaryResponseContent(httpx.Response(200)))
async def test_azure_text_to_audio_get_audio_contents(mock_speech_create, azure_openai_unit_test_env) -> None:
    openai_audio_to_text = AzureTextToAudio()

    audio_contents = await openai_audio_to_text.get_audio_contents("Hello World!")
    assert len(audio_contents) == 1
    assert audio_contents[0].ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME"]
