# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Literal

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError

logger = logging.getLogger(__name__)


class OpenAITextToAudioExecutionSettings(PromptExecutionSettings):
    """Request settings for OpenAI text to audio services."""

    ai_model_id: str | None = Field(None, serialization_alias="model")
    input: str | None = Field(
        None, description="Do not set this manually. It is set by the service based on the text content."
    )
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "alloy"
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] | None = None
    speed: float | None = None

    @model_validator(mode="after")
    def validate_speed(self) -> "OpenAITextToAudioExecutionSettings":
        """Validate the speed parameter."""
        if self.speed is not None and (self.speed < 0.25 or self.speed > 4.0):
            raise ServiceInvalidExecutionSettingsError("Speed must be between 0.25 and 4.0.")
        return self
