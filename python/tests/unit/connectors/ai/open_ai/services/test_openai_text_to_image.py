# Copyright (c) Microsoft. All rights reserved.

import warnings
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncClient
from openai.resources.images import AsyncImages
from openai.types.image import Image
from openai.types.images_response import ImagesResponse

from semantic_kernel.connectors.ai.open_ai import OpenAITextToImage, OpenAITextToImageExecutionSettings
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceResponseException,
)


def test_init(openai_unit_test_env):
    openai_text_to_image = OpenAITextToImage()

    assert openai_text_to_image.client is not None
    assert isinstance(openai_text_to_image.client, AsyncClient)
    assert openai_text_to_image.ai_model_id == openai_unit_test_env["OPENAI_TEXT_TO_IMAGE_MODEL_ID"]


def test_init_validation_fail() -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextToImage(api_key="34523", ai_model_id={"test": "dict"})


def test_init_to_from_dict(openai_unit_test_env):
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
    with pytest.raises(ServiceInitializationError):
        OpenAITextToImage(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_TEXT_TO_IMAGE_MODEL_ID"]], indirect=True)
def test_init_with_no_model_id(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextToImage(
            env_file_path="test.env",
        )


def test_prompt_execution_settings_class(openai_unit_test_env) -> None:
    openai_text_to_image = OpenAITextToImage()
    assert openai_text_to_image.get_prompt_execution_settings_class() == OpenAITextToImageExecutionSettings


@patch.object(AsyncImages, "generate", return_value=AsyncMock(spec=ImagesResponse))
async def test_generate_calls_with_parameters(mock_generate, openai_unit_test_env) -> None:
    mock_generate.return_value.data = [Image(url="abc")]

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
        )
        assert len(w) == 2


@patch.object(AsyncImages, "generate", new_callable=AsyncMock, side_effect=Exception)
async def test_generate_fail(mock_generate, openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    width = 512

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceResponseException):
        await openai_text_to_image.generate_image(description="painting of flowers in vase", width=width, height=width)


async def test_generate_invalid_image_size(openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    width = 100

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await openai_text_to_image.generate_image(description="painting of flowers in vase", width=width, height=width)


async def test_generate_empty_description(openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    width = 100

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await openai_text_to_image.generate_image(description="", width=width, height=width)


@patch.object(AsyncImages, "generate", new_callable=AsyncMock)
async def test_generate_no_result(mock_generate, openai_unit_test_env) -> None:
    mock_generate.return_value = ImagesResponse(created=0, data=[])
    ai_model_id = "test_model_id"
    width = 512

    openai_text_to_image = OpenAITextToImage(ai_model_id=ai_model_id)
    with pytest.raises(ServiceResponseException):
        await openai_text_to_image.generate_image(description="painting of flowers in vase", width=width, height=width)
