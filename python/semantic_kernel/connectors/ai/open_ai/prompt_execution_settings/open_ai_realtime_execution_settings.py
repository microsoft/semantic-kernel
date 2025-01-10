# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from typing import Annotated, Any, Literal

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputAudioTranscription(KernelBaseModel):
    """Input audio transcription settings."""

    model: Literal["whisper-1"] | None = None


class TurnDetection(KernelBaseModel):
    """Turn detection settings."""

    type: Literal["server_vad"] | None = None
    threshold: Annotated[float | None, Field(ge=0, le=1)] = None
    prefix_padding_ms: Annotated[int | None, Field(ge=0)] = None
    silence_duration_ms: Annotated[int | None, Field(ge=0)] = None
    create_response: bool | None = None


class OpenAIRealtimeExecutionSettings(PromptExecutionSettings):
    """Request settings for OpenAI realtime services."""

    modalities: Sequence[Literal["audio", "text"]] | None = None
    ai_model_id: Annotated[str | None, Field(None, serialization_alias="model")] = None
    instructions: str | None = None
    voice: str | None = None
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | None = None
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | None = None
    input_audio_transcription: InputAudioTranscription | None = None
    turn_detection: TurnDetection | None = None
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    tool_choice: Annotated[
        str | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    max_response_output_tokens: Annotated[int | Literal["inf"] | None, Field(gt=0)] = None
