# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError

from semantic_kernel.connectors.ai.audio_to_text_client_base import AudioToTextClientBase
from semantic_kernel.connectors.ai.camb.camb_prompt_execution_settings import CambAudioToTextExecutionSettings
from semantic_kernel.connectors.ai.camb.settings.camb_settings import CambSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidRequestError,
    ServiceInvalidResponseError,
)

logger: logging.Logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 2.0
_MAX_POLL_ATTEMPTS = 120


class CambAudioToText(AudioToTextClientBase):
    """Camb.ai audio-to-text (transcription) service."""

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
        """Initialize the CambAudioToText service.

        Args:
            api_key: The camb.ai API key. If not provided, reads from CAMB_API_KEY env var.
            ai_model_id: The model identifier. Defaults to "camb-transcription".
            service_id: The service ID. Defaults to ai_model_id.
            async_client: An optional pre-configured AsyncCambAI client.
            env_file_path: Path to a .env file for settings.
            env_file_encoding: Encoding of the .env file.
        """
        try:
            camb_settings = CambSettings(
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create camb.ai settings.", ex) from ex

        resolved_model_id = ai_model_id or "camb-transcription"

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
    async def get_text_contents(
        self,
        audio_content: AudioContent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[TextContent]:
        """Transcribe audio to text using camb.ai.

        Args:
            audio_content: The audio content to transcribe. Must have a uri (file path) or data (bytes).
            settings: Optional execution settings (language, etc.).
            **kwargs: Additional keyword arguments.

        Returns:
            A list containing a single TextContent with the transcription.
        """
        if not settings:
            settings = CambAudioToTextExecutionSettings()
        elif not isinstance(settings, CambAudioToTextExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)

        assert isinstance(settings, CambAudioToTextExecutionSettings)  # nosec

        # Build kwargs for create_transcription
        create_kwargs: dict[str, Any] = {}

        # language is required by the API
        create_kwargs["language"] = settings.language if settings.language is not None else 1

        # Get audio file — pass as tuple with filename for proper content-type detection
        if audio_content.uri and isinstance(audio_content.uri, str):
            import os

            filename = os.path.basename(audio_content.uri)
            with open(audio_content.uri, "rb") as f:
                audio_bytes = f.read()
            create_kwargs["media_file"] = (filename, audio_bytes)
        elif audio_content.data:
            audio_bytes = audio_content.data if isinstance(audio_content.data, bytes) else bytes(audio_content.data)
            create_kwargs["media_file"] = ("audio.wav", audio_bytes)
        else:
            raise ServiceInvalidRequestError("Audio content must have a uri (file path) or data (bytes).")

        # Create transcription task
        task_result = await self.async_client.transcription.create_transcription(**create_kwargs)
        task_id = task_result.task_id

        # Poll for completion
        run_id = await self._poll_task_status(task_id)

        # Fetch transcription result
        result = await self.async_client.transcription.get_transcription_result(run_id)

        # TranscriptionResult has a .transcript list of Transcript objects, each with .text
        if hasattr(result, "transcript") and isinstance(result.transcript, list):
            full_text = " ".join(seg.text for seg in result.transcript if hasattr(seg, "text"))
        elif hasattr(result, "text"):
            full_text = result.text
        else:
            full_text = str(result)

        return [
            TextContent(
                ai_model_id=self.ai_model_id,
                text=full_text,
                inner_content=result,
            )
        ]

    async def _poll_task_status(self, task_id: str) -> str:
        """Poll the transcription task until completion.

        Args:
            task_id: The task ID to poll.

        Returns:
            The run_id of the completed task.

        Raises:
            ServiceInvalidResponseError: If polling times out or the task fails.
        """
        for _ in range(_MAX_POLL_ATTEMPTS):
            status = await self.async_client.transcription.get_transcription_task_status(task_id)
            if hasattr(status, "status") and status.status in {"SUCCESS", "completed"}:
                return status.run_id
            if hasattr(status, "status") and status.status in {"FAILED", "failed", "ERROR", "error"}:
                raise ServiceInvalidResponseError(f"Camb.ai transcription task failed: {status}")
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        raise ServiceInvalidResponseError("Camb.ai transcription task timed out.")

    @override
    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Get the request settings class."""
        return CambAudioToTextExecutionSettings
