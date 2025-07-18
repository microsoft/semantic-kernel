# Copyright (c) Microsoft. All rights reserved.

import os
import warnings
from unittest.mock import AsyncMock, patch

import pydantic
import pytest
from openai import AsyncClient
from openai.resources.images import AsyncImages
from openai.types.image import Image
from openai.types.images_response import ImagesResponse

from semantic_kernel.connectors.ai.open_ai import OpenAITextToImage, OpenAITextToImageExecutionSettings
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_to_image_base import OpenAITextToImageBase
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidRequestError,
    ServiceResponseException,
)

sample_img = os.path.join(os.path.dirname(__file__), "../../../../../assets/sample_image.jpg")


def test_init(openai_unit_test_env):
    """Test that OpenAITextToImage initializes with the correct model id and client."""
    openai_text_to_image = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])

    assert openai_text_to_image.client is not None
    assert isinstance(openai_text_to_image.client, AsyncClient)
    assert openai_text_to_image.ai_model_id == openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"]


@pytest.mark.parametrize("exclude_list", [["OPENAI_TEXT_TO_IMAGE_MODEL_ID"]], indirect=True)
def test_init_validation_fail(openai_unit_test_env) -> None:
    """Test that initialization fails when required parameters are missing."""
    with pytest.raises(ServiceInitializationError):
        OpenAITextToImage(api_key="34523", ai_model_id=None, env_file_path="test.env")


def test_init_to_from_dict(openai_unit_test_env):
    """Test to_dict and from_dict methods for correct serialization and deserialization."""
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }
    text_to_image = OpenAITextToImage.from_dict(settings)
    dumped_settings = text_to_image.to_dict()
    assert dumped_settings["ai_model_id"] == settings["ai_model_id"]
    assert dumped_settings["api_key"] == settings["api_key"]


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(openai_unit_test_env) -> None:
    """Test that initialization fails when API key is missing."""
    with pytest.raises(ServiceInitializationError):
        OpenAITextToImage(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_TEXT_TO_IMAGE_MODEL_ID"]], indirect=True)
def test_init_with_no_model_id(openai_unit_test_env) -> None:
    """Test that initialization fails when model id is missing."""
    with pytest.raises(ServiceInitializationError):
        OpenAITextToImage(
            env_file_path="test.env",
        )


def test_prompt_execution_settings_class(openai_unit_test_env) -> None:
    """Test that the correct prompt execution settings class is returned."""
    openai_text_to_image = OpenAITextToImage()
    assert openai_text_to_image.get_prompt_execution_settings_class() == OpenAITextToImageExecutionSettings


@patch.object(AsyncImages, "generate", new_callable=AsyncMock)
async def test_generate_calls_with_parameters(mock_generate, openai_unit_test_env) -> None:
    """Test that generate_image calls the OpenAI API with correct parameters."""
    mock_response = ImagesResponse(created=1, data=[Image(url="abc")], usage=None)
    mock_generate.return_value = mock_response

    ai_model_id = "test_model_id"
    prompt = "painting of flowers in vase"
    width = 512

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)

    with warnings.catch_warnings(record=True) as w:
        await openai_text_to_image.generate_image(description=prompt, width=width, height=width)

        mock_generate.assert_awaited_once_with(
            prompt=prompt,
            model=ai_model_id,
            size=f"{width}x{width}",
            n=1,
        )
        assert len(w) == 3


@patch.object(AsyncImages, "generate", new_callable=AsyncMock, side_effect=Exception)
async def test_generate_fail(mock_generate, openai_unit_test_env) -> None:
    """Test that generate_image raises ServiceResponseException on API failure."""
    ai_model_id = "test_model_id"
    width = 512

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceResponseException):
        await openai_text_to_image.generate_image(description="painting of flowers in vase", width=width, height=width)


async def test_generate_invalid_image_size(openai_unit_test_env) -> None:
    """Test that invalid image size raises ServiceInvalidExecutionSettingsError."""
    ai_model_id = "test_model_id"
    width = 100

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await openai_text_to_image.generate_image(description="painting of flowers in vase", width=width, height=width)


async def test_generate_empty_description(openai_unit_test_env) -> None:
    """Test that empty description raises ServiceInvalidExecutionSettingsError."""
    ai_model_id = "test_model_id"
    width = 100

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await openai_text_to_image.generate_image(description="", width=width, height=width)


@patch.object(AsyncImages, "generate", new_callable=AsyncMock)
async def test_generate_no_result(mock_generate, openai_unit_test_env) -> None:
    """Test that no result from API raises ServiceResponseException."""
    mock_generate.return_value = ImagesResponse(created=0, data=[], usage=None)
    ai_model_id = "test_model_id"
    width = 512

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceResponseException):
        await openai_text_to_image.generate_image(description="painting of flowers in vase", width=width, height=width)


@patch.object(OpenAITextToImageBase, "_send_image_edit_request", new_callable=AsyncMock)
async def test_edit_image_with_path_success(mock_edit, openai_unit_test_env):
    """Test editing an image using a file path returns the expected URL."""
    mock_edit.return_value = ImagesResponse(created=1, data=[Image(url="edited_url")], usage=None)
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    result = await service.edit_image(
        prompt="edit this image",
        image_paths=[sample_img],
    )
    assert result == ["edited_url"]
    mock_edit.assert_awaited()


@patch.object(OpenAITextToImageBase, "_send_image_edit_request", new_callable=AsyncMock)
async def test_edit_image_with_file_success(mock_edit, openai_unit_test_env):
    """Test editing an image using a file object returns the expected URL."""
    mock_edit.return_value = ImagesResponse(created=1, data=[Image(url="edited_url")], usage=None)
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    with open(sample_img, "rb") as f:
        result = await service.edit_image(
            prompt="edit this image",
            image_files=[f],
        )
    assert result == ["edited_url"]
    mock_edit.assert_awaited()


@patch.object(OpenAITextToImageBase, "_send_image_edit_request", new_callable=AsyncMock)
async def test_edit_image_with_mask_path_and_file(mock_edit, openai_unit_test_env):
    """Test editing an image with both mask path and mask file returns the expected URL."""
    mock_edit.return_value = ImagesResponse(created=1, data=[Image(url="edited_url")], usage=None)
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    # mask_path
    result = await service.edit_image(
        prompt="edit with mask",
        image_paths=[sample_img],
        mask_path=sample_img,
    )
    assert result == ["edited_url"]
    # mask_file
    with open(sample_img, "rb") as mf:
        result2 = await service.edit_image(
            prompt="edit with mask",
            image_paths=[sample_img],
            mask_file=mf,
        )
    assert result2 == ["edited_url"]


@pytest.mark.asyncio
async def test_edit_image_prompt_required(openai_unit_test_env):
    """Test that an empty prompt raises ServiceInvalidRequestError."""
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    with pytest.raises(ServiceInvalidRequestError):
        await service.edit_image(prompt="", image_paths=[sample_img])


@pytest.mark.asyncio
async def test_edit_image_both_path_and_file_error(openai_unit_test_env):
    """Test that providing both image_paths and image_files raises ServiceInvalidRequestError."""
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    with (
        open(sample_img, "rb") as f,
        pytest.raises(ServiceInvalidRequestError),
    ):
        await service.edit_image(
            prompt="edit",
            image_paths=[sample_img],
            image_files=[f],
        )


@patch.object(OpenAITextToImageBase, "_send_image_edit_request", new_callable=AsyncMock)
async def test_edit_image_no_valid_data_in_response(mock_edit, openai_unit_test_env):
    """Test that no valid data in edit response raises ServiceResponseException."""
    mock_edit.return_value = ImagesResponse(created=1, data=[], usage=None)
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    with pytest.raises(ServiceResponseException):
        await service.edit_image(
            prompt="edit",
            image_paths=[sample_img],
        )


@patch.object(OpenAITextToImageBase, "_send_request", new_callable=AsyncMock)
async def test_generate_images_with_n_parameter(mock_generate, openai_unit_test_env):
    """Test that generate_images returns correct URLs when n parameter is set."""
    mock_generate.return_value = ImagesResponse(created=3, data=[Image(url=f"url_{i}") for i in range(3)], usage=None)
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    settings = OpenAITextToImageExecutionSettings(n=3)
    result = await service.generate_images("prompt", settings=settings)
    assert result == [f"url_{i}" for i in range(3)]


@patch.object(OpenAITextToImageBase, "_send_request", new_callable=AsyncMock)
async def test_generate_images_with_output_compression_and_background(mock_generate, openai_unit_test_env):
    """Test that output_compression and background parameters are handled correctly."""
    mock_generate.return_value = ImagesResponse(created=1, data=[Image(url="url")], usage=None)
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    settings = OpenAITextToImageExecutionSettings(output_compression=5, background="transparent")
    await service.generate_images("prompt", settings=settings)
    called_settings = mock_generate.call_args[0][0]
    assert called_settings.output_compression == 5
    assert called_settings.background == "transparent"


@patch.object(OpenAITextToImageBase, "store_usage")
def test_store_usage_for_images_response(mock_store_usage, openai_unit_test_env):
    """Test that store_usage is called for ImagesResponse."""
    service = OpenAITextToImage(ai_model_id=openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"])
    response = ImagesResponse(created=1, data=[Image(url="url")], usage=None)
    service.store_usage(response)
    mock_store_usage.assert_called()


@pytest.mark.asyncio
async def test_edit_image_invalid_n_parameter():
    """Test that invalid n parameter raises pydantic.ValidationError."""
    with pytest.raises(pydantic.ValidationError):
        OpenAITextToImageExecutionSettings(n=0)
    with pytest.raises(pydantic.ValidationError):
        OpenAITextToImageExecutionSettings(n=11)
