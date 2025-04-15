# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.images import AsyncImages
from openai.types.image import Image
from openai.types.images_response import ImagesResponse

from semantic_kernel.connectors.ai.open_ai.services.azure_text_to_image import AzureTextToImage
from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_azure_text_to_image_init(azure_openai_unit_test_env) -> None:
    # Test successful initialization
    azure_text_to_image = AzureTextToImage()

    assert azure_text_to_image.client is not None
    assert isinstance(azure_text_to_image.client, AsyncAzureOpenAI)
    assert azure_text_to_image.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME"]
    assert isinstance(azure_text_to_image, TextToImageClientBase)


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_text_to_image_init_with_empty_deployment_name(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextToImage(env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_text_to_image_init_with_empty_api_key(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextToImage(env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BASE_URL"]], indirect=True)
def test_azure_text_to_image_init_with_empty_endpoint_and_base_url(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextToImage(env_file_path="test.env")


@pytest.mark.parametrize("override_env_param_dict", [{"AZURE_OPENAI_ENDPOINT": "http://test.com"}], indirect=True)
def test_azure_text_to_image_init_with_invalid_endpoint(azure_openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AzureTextToImage()


@pytest.mark.parametrize(
    "override_env_param_dict",
    [{"AZURE_OPENAI_BASE_URL": "https://test_text_to_image_deployment.test-base-url.com"}],
    indirect=True,
)
def test_azure_text_to_image_init_with_from_dict(azure_openai_unit_test_env) -> None:
    default_headers = {"test_header": "test_value"}

    settings = {
        "deployment_name": azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME"],
        "endpoint": azure_openai_unit_test_env["AZURE_OPENAI_ENDPOINT"],
        "api_key": azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"],
        "api_version": azure_openai_unit_test_env["AZURE_OPENAI_API_VERSION"],
        "default_headers": default_headers,
    }

    azure_text_to_image = AzureTextToImage.from_dict(settings=settings)

    assert azure_text_to_image.client is not None
    assert isinstance(azure_text_to_image.client, AsyncAzureOpenAI)
    assert azure_text_to_image.ai_model_id == azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME"]
    assert isinstance(azure_text_to_image, TextToImageClientBase)
    assert settings["deployment_name"] in str(azure_text_to_image.client.base_url)
    assert azure_text_to_image.client.api_key == azure_openai_unit_test_env["AZURE_OPENAI_API_KEY"]

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in azure_text_to_image.client.default_headers
        assert azure_text_to_image.client.default_headers[key] == value


@patch.object(AsyncImages, "generate", return_value=AsyncMock(spec=ImagesResponse))
async def test_azure_text_to_image_calls_with_parameters(mock_generate, azure_openai_unit_test_env) -> None:
    mock_generate.return_value.data = [Image(url="abc")]

    prompt = "A painting of a vase with flowers"
    width = 512

    azure_text_to_image = AzureTextToImage()
    await azure_text_to_image.generate_image(prompt, width=width, height=width)

    mock_generate.assert_awaited_once_with(
        prompt=prompt,
        model=azure_openai_unit_test_env["AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME"],
        size=f"{width}x{width}",
    )
