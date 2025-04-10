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
    ai_model_id: str | None = Field(default=None, serialization_alias="model")
    size: ImageSize | None = None
    quality: str | None = None
    style: str | None = None

    @model_validator(mode="before")
    @classmethod
    def get_size(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Check that the requested image size is valid."""
        if isinstance(data, dict):
            if "size" not in data and "width" in data and "height" in data:
                data["size"] = ImageSize(width=data["width"], height=data["height"])
            elif "extension_data" in data:
                extension_data = data["extension_data"]
                if (
                    isinstance(extension_data, dict)
                    and "size" not in extension_data
                    and "width" in extension_data
                    and "height" in extension_data
                ):
                    data["extension_data"]["size"] = ImageSize(
                        width=extension_data["width"], height=extension_data["height"]
                    )
        return data

    @model_validator(mode="after")
    def check_size(self) -> "OpenAITextToImageExecutionSettings":
        """Check that the requested image size is valid."""
        size = self.size or self.extension_data.get("size")

        if size is not None and (size.width, size.height) not in VALID_IMAGE_SIZES:
            raise ServiceInvalidExecutionSettingsError(f"Invalid image size: {size.width}x{size.height}.")

        return self

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings dictionary for the OpenAI API."""
        settings_dict = super().prepare_settings_dict(**kwargs)

        if self.size is not None:
            settings_dict["size"] = str(self.size)

        return settings_dict
