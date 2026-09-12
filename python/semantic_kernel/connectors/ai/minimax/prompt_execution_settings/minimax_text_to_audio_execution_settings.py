# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class MiniMaxTextToAudioExecutionSettings(PromptExecutionSettings):
    """Request settings for MiniMax text-to-audio (T2A v2)."""

    ai_model_id: str | None = Field(None, serialization_alias="model")
    input: str | None = Field(None, serialization_alias="text")
    stream: bool | None = None
    language_boost: str | None = None
    output_format: str | None = None
    voice_setting: dict[str, Any] | None = None
    pronunciation_dict: dict[str, Any] | None = None
    audio_setting: dict[str, Any] | None = None
    voice_modify: dict[str, Any] | None = None
    subtitle_enable: bool | None = None
