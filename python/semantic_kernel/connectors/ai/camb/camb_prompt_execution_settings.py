# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class CambTextToAudioExecutionSettings(PromptExecutionSettings):
    """Request settings for camb.ai text-to-speech services."""

    voice_id: int | None = None
    language: str | None = None
    output_format: Literal["pcm_s16le", "wav", "flac", "mp3", "ogg", "mulaw"] | None = None
    user_instructions: str | None = Field(default=None, max_length=1000)


class CambAudioToTextExecutionSettings(PromptExecutionSettings):
    """Request settings for camb.ai audio-to-text (transcription) services."""

    language: int | None = None
