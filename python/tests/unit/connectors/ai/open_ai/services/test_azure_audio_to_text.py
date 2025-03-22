# Copyright (c) Microsoft. All rights reserved.

import os
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.audio.transcriptions import AsyncTranscriptions
from openai.types.audio import Transcription

from semantic_kernel.connectors.ai.open_ai import AzureAudioToText
from semantic_kernel.contents import AudioContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidRequestError


def test_azure_audio_to_text_init(azure_openai_unit_test_env) -> None:
    azure_audio_to_text = AzureAudioToText()

    assert azure_audio_to_text.client is not None
    assert isinstance(azure_audio_to_text.client, AsyncAzureOpenAI)
    assert azure_audio_to_text.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME"]


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_audio_to_text_init_with_empty_deployment_name(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="The Azure OpenAI audio to text deployment name is required."):
        AzureAudioToText(env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_audio_to_text_init_with_empty_api_key(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureAudioToText(env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_azure_audio_to_text_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="Please provide an endpoint or a base_url"):
        AzureAudioToText(env_file_path="test.env")


@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
def test_azure_audio_to_text_init_with_invalid_http_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="Invalid settings: "):
        AzureAudioToText()


@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"AZURE_OPENAI_BASE_URL": "https://test_audio_to_text_deployment.test-base-url.com"}],
    indirect=True,
)
def test_azure_audio_to_text_init_with_from_dict(azure_openai_unit_test_env) -> None:
    default_headers = {"test_header": "test_value"}

    settings = {
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME"],
        "endpoint": azure_openai_unit_test_env["AZURE_OPENAI_ENDPOINT"],
        "api_key": azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"],
        "api_version": azure_openai_unit_test_env["AZURE_OPENAI_API_VERSION"],
        "default_headers": default_headers,
    }

    azure_audio_to_text = AzureAudioToText.from_dict(settings=settings)

    assert azure_audio_to_text.client is not None
    assert isinstance(azure_audio_to_text.client, AsyncAzureOpenAI)
    assert azure_audio_to_text.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME"]
    assert settings["deployment_name"] in str(azure_audio_to_text.client.base_url)
    assert azure_audio_to_text.client.api_key == azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"]

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in azure_audio_to_text.client.default_headers
        assert azure_audio_to_text.client.default_headers[key] == value


async def test_azure_audio_to_text_get_text_contents(azure_openai_unit_test_env) -> None:
    audio_content = AudioContent.from_audio_file(
        os.path.join(os.path.dirname(__file__), "../../../../../", "assets/sample_audio.mp3")
    )

    with patch.object(AsyncTranscriptions, "create", new_callable=AsyncMock) as mock_transcription_create:
        mock_transcription_create.return_value = Transcription(text="This is a test audio file.")

        openai_audio_to_text = AzureAudioToText()

        text_contents = await openai_audio_to_text.get_text_contents(audio_content)
        assert len(text_contents) == 1
        assert text_contents[0].text == "This is a test audio file."
        assert text_contents[0].ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME"]


async def test_azure_audio_to_text_get_text_contents_invalid_audio_content(azure_openai_unit_test_env):
    audio_content = AudioContent()

    openai_audio_to_text = AzureAudioToText()
    with pytest.raises(ServiceInvalidRequestError, match="Audio content uri must be a string to a local file."):
        await openai_audio_to_text.get_text_contents(audio_content)
