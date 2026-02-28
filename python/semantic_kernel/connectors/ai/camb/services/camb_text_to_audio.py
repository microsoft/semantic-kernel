# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError

from semantic_kernel.connectors.ai.camb.camb_prompt_execution_settings import CambTextToAudioExecutionSettings
from semantic_kernel.connectors.ai.camb.settings.camb_settings import CambSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_to_audio_client_base import TextToAudioClientBase
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)

# Mime type mapping for audio formats
_FORMAT_MIME_TYPES: dict[str, str] = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
    "pcm_s16le": "audio/pcm",
    "mulaw": "audio/basic",
}


class CambTextToAudio(TextToAudioClientBase):
    """Camb.ai text-to-speech service using the MARS TTS models."""

    async_client: Any = None

    def __init__(
        self,
        api_key: str | None = None,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        async_client: Any | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the CambTextToAudio service.

        Args:
            api_key: The camb.ai API key. If not provided, reads from CAMB_API_KEY env var.
            ai_model_id: The TTS model ID (e.g. "mars-flash", "mars-pro"). Defaults to "mars-flash".
            service_id: The service ID. Defaults to ai_model_id.
            async_client: An optional pre-configured AsyncCambAI client.
            env_file_path: Path to a .env file for settings.
            env_file_encoding: Encoding of the .env file.
        """
        try:
            camb_settings = CambSettings(
                api_key=api_key,
                text_to_audio_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create camb.ai settings.", ex) from ex

        resolved_model_id = ai_model_id or camb_settings.text_to_audio_model_id or "mars-flash"

        if async_client is None:
            try:
                from camb.client import AsyncCambAI
            except ImportError:
                raise ServiceInitializationError(
                    "The camb package is required. Install it with: pip install semantic-kernel[camb]"
                )
            async_client = AsyncCambAI(api_key=camb_settings.api_key.get_secret_value())

        super().__init__(
            service_id=service_id or resolved_model_id,
            ai_model_id=resolved_model_id,
            async_client=async_client,
        )

    @override
    async def get_audio_contents(
        self,
        text: str,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[AudioContent]:
        """Generate audio from text using camb.ai TTS.

        Args:
            text: The text to synthesize into speech.
            settings: Optional execution settings (voice_id, language, etc.).
            **kwargs: Additional keyword arguments.

        Returns:
            A list containing a single AudioContent with the generated audio.
        """
        if not settings:
            settings = CambTextToAudioExecutionSettings()
        elif not isinstance(settings, CambTextToAudioExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)

        assert isinstance(settings, CambTextToAudioExecutionSettings)  # nosec

        tts_kwargs: dict[str, Any] = {
            "text": text,
            "speech_model": self.ai_model_id,
        }

        if settings.voice_id is not None:
            tts_kwargs["voice_id"] = settings.voice_id
        if settings.language is not None:
            tts_kwargs["language"] = settings.language

        output_format = settings.output_format or "wav"

        try:
            from camb import StreamTtsOutputConfiguration

            tts_kwargs["output_configuration"] = StreamTtsOutputConfiguration(format=output_format)
        except ImportError:
            tts_kwargs["output_configuration"] = {"format": output_format}

        if settings.user_instructions is not None:
            tts_kwargs["user_instructions"] = settings.user_instructions

        audio_chunks: list[bytes] = []
        async for chunk in self.async_client.text_to_speech.tts(**tts_kwargs):
            audio_chunks.append(chunk)

        audio_data = b"".join(audio_chunks)
        mime_type = _FORMAT_MIME_TYPES.get(output_format, "audio/wav")

        return [
            AudioContent(
                ai_model_id=self.ai_model_id,
                data=audio_data,
                data_format="base64",
                mime_type=mime_type,
            )
        ]

    @override
    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Get the request settings class."""
        return CambTextToAudioExecutionSettings
