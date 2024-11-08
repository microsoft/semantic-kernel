# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


VALID_IMAGE_SIZES = [
    (256, 256),
    (512, 512),
    (1024, 1024),
    (1792, 1024),
    (1024, 1792),
]


class ImageSize(KernelBaseModel):
    """Image size."""

    width: int
    height: int

    def __str__(self) -> str:
        """Return the string representation of the image size."""
        return f"{self.width}x{self.height}"


class OpenAITextToImageExecutionSettings(PromptExecutionSettings):
    """Request settings for OpenAI text to image services."""

    prompt: str | None = None
    ai_model_id: str | None = Field(None, serialization_alias="model")
    size: ImageSize | None = None
    quality: str | None = None
    style: str | None = None

    @model_validator(mode="after")
    def check_size(self) -> "OpenAITextToImageExecutionSettings":
        """Check that the requested image size is valid."""
        size = self.size or self.extension_data.get("size")

        if size is not None and (size.width, size.height) not in VALID_IMAGE_SIZES:
            raise ServiceInvalidExecutionSettingsError(f"Invalid image size: {size.width}x{size.height}.")

        return self

    @model_validator(mode="after")
    def check_prompt(self) -> "OpenAITextToImageExecutionSettings":
        """Check that the prompt is not empty."""
        prompt = self.prompt or self.extension_data.get("prompt")

        if not prompt:
            raise ServiceInvalidExecutionSettingsError("The prompt is required.")

        return self

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings dictionary for the OpenAI API."""
        settings_dict = super().prepare_settings_dict(**kwargs)

        if self.size is not None:
            settings_dict["size"] = str(self.size)

        return settings_dict
