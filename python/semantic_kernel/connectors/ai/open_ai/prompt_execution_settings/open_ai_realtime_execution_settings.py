# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping, Sequence
from typing import Annotated, Any, Literal

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputAudioTranscription(KernelBaseModel):
    """Input audio transcription settings.

    Args:
        model: The model to use for transcription, should be one of the following:
            - whisper-1
            - gpt-4o-transcribe
            - gpt-4o-mini-transcribe
        language: The language of the audio, should be in ISO-639-1 format, like 'en'.
        prompt: An optional text to guide the model's style or continue a previous audio segment.
            The prompt should match the audio language.
    """

    model: Literal["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"] | None = None
    language: str | None = None
    prompt: str | None = None


class TurnDetection(KernelBaseModel):
    """Turn detection settings.

    Args:
        type: The type of turn detection, server_vad or semantic_vad.
        create_response: Whether to create a response for each detected turn.
        eagerness: The eagerness of the voice activity detection, can be low, medium, high, or auto,
            used only for semantic_vad.
        interrupt_response: Whether to interrupt the response for each detected turn.
        prefix_padding_ms: The padding before the detected voice activity, in milliseconds.
        silence_duration_ms: The duration of silence to detect the end of a turn, in milliseconds.
        threshold: The threshold for voice activity detection, should be between 0 and 1, only for server_vad.

    """

    type: Literal["server_vad", "semantic_vad"] = "server_vad"
    create_response: bool | None = None
    eagerness: Literal["low", "medium", "high", "auto"] | None = None
    interrupt_response: bool | None = None
    prefix_padding_ms: Annotated[int | None, Field(ge=0)] = None
    silence_duration_ms: Annotated[int | None, Field(ge=0)] = None
    threshold: Annotated[float | None, Field(ge=0.0, le=1.0)] = None


class OpenAIRealtimeExecutionSettings(PromptExecutionSettings):
    """Request settings for OpenAI realtime services."""

    modalities: Sequence[Literal["audio", "text"]] | None = None
    ai_model_id: Annotated[str | None, Field(None, serialization_alias="model")] = None
    instructions: str | None = None
    voice: str | None = None
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | None = None
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | None = None
    input_audio_transcription: InputAudioTranscription | Mapping[str, str] | None = None
    turn_detection: TurnDetection | Mapping[str, str] | None = None
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
    temperature: Annotated[float | None, Field(ge=0.6, le=1.2)] = None
    max_response_output_tokens: Annotated[int | Literal["inf"] | None, Field(gt=0)] = None
    input_audio_noise_reduction: dict[Literal["type"], Literal["near_field", "far_field"]] | None = None


class AzureRealtimeExecutionSettings(OpenAIRealtimeExecutionSettings):
    """Request settings for Azure OpenAI realtime services."""

    pass
