# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import json
import logging
import os
from typing import Annotated, Any

from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 2.0
_MAX_POLL_ATTEMPTS = 120


class CambPlugin(KernelBaseModel):
    """A plugin that provides camb.ai audio and translation functionality.

    Exposes six kernel functions for features that don't have existing
    Semantic Kernel base classes: translate, translated_tts, clone_voice,
    list_voices, text_to_sound, and separate_audio.

    Usage:
        kernel.add_plugin(CambPlugin(api_key="your-key"), "camb")
    """

    async_client: Any = None

    def __init__(
        self,
        api_key: str | None = None,
        async_client: Any | None = None,
    ) -> None:
        """Initialize the CambPlugin.

        Args:
            api_key: The camb.ai API key. If not provided, reads from CAMB_API_KEY env var.
            async_client: An optional pre-configured AsyncCambAI client.
        """
        if async_client is None:
            resolved_key = api_key or os.environ.get("CAMB_API_KEY")
            if not resolved_key:
                raise FunctionExecutionException(
                    "A camb.ai API key is required. Provide api_key or set CAMB_API_KEY env var."
                )
            try:
                from camb.client import AsyncCambAI
            except ImportError:
                raise FunctionExecutionException(
                    "The camb package is required. Install it with: pip install semantic-kernel[camb]"
                )
            async_client = AsyncCambAI(api_key=resolved_key)

        super().__init__(async_client=async_client)

    async def _poll_task_status(self, get_status_fn: Any, task_id: str) -> str:
        """Poll an async task until completion.

        Args:
            get_status_fn: An async callable that takes task_id and returns a status object.
            task_id: The task ID to poll.

        Returns:
            The run_id of the completed task.

        Raises:
            FunctionExecutionException: If the task fails or times out.
        """
        for _ in range(_MAX_POLL_ATTEMPTS):
            status = await get_status_fn(task_id)
            if hasattr(status, "status") and status.status in {"SUCCESS", "completed"}:
                return status.run_id
            if hasattr(status, "status") and status.status in {"FAILED", "failed", "ERROR", "error"}:
                raise FunctionExecutionException(f"Camb.ai task failed: {status}")
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        raise FunctionExecutionException("Camb.ai task timed out.")

    @kernel_function(description="Translate text between 140+ languages using camb.ai", name="translate")
    async def translate(
        self,
        text: Annotated[str, "The text to translate."],
        source_language: Annotated[int, "Source language ID (e.g. 1=English, 2=Spanish)."],
        target_language: Annotated[int, "Target language ID (e.g. 1=English, 2=Spanish)."],
        formality: Annotated[int | None, "Formality level (optional)."] = None,
    ) -> str:
        """Translate text between languages using camb.ai.

        Args:
            text: The text to translate.
            source_language: Source language ID (e.g. 1=English, 2=Spanish).
            target_language: Target language ID.
            formality: Optional formality level.

        Returns:
            The translated text.
        """
        kwargs: dict[str, Any] = {
            "text": text,
            "source_language": source_language,
            "target_language": target_language,
        }
        if formality is not None:
            kwargs["formality"] = formality

        try:
            result = await self.async_client.translation.translation_stream(**kwargs)
            return str(result)
        except Exception as e:
            # The SDK has a known bug where successful 200 responses may raise ApiError
            if hasattr(e, "status_code") and e.status_code == 200 and hasattr(e, "body") and e.body:
                return str(e.body)
            raise FunctionExecutionException(f"Camb.ai translation failed: {e}") from e

    @kernel_function(description="Translate text and generate speech in one operation using camb.ai", name="translated_tts")
    async def translated_tts(
        self,
        text: Annotated[str, "The text to translate and speak."],
        source_language: Annotated[int, "Source language ID."],
        target_language: Annotated[int, "Target language ID."],
        voice_id: Annotated[int, "The voice ID to use for speech synthesis."],
    ) -> str:
        """Translate text and generate speech in one operation.

        Args:
            text: The text to translate and speak.
            source_language: Source language ID.
            target_language: Target language ID.
            voice_id: The voice ID to use.

        Returns:
            JSON string with base64-encoded audio and format info.
        """
        import httpx

        task_result = await self.async_client.translated_tts.create_translated_tts(
            text=text,
            source_language=source_language,
            target_language=target_language,
            voice_id=voice_id,
        )

        run_id = await self._poll_task_status(
            self.async_client.translated_tts.get_translated_tts_task_status,
            task_result.task_id,
        )

        # Fetch audio via HTTP endpoint
        api_key = ""
        if hasattr(self.async_client, "_client_wrapper"):
            api_key = getattr(self.async_client._client_wrapper, "api_key", "")
        elif hasattr(self.async_client, "_api_key"):
            api_key = self.async_client._api_key
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"https://client.camb.ai/apis/tts-result/{run_id}",
                headers={"x-api-key": api_key},
            )
            response.raise_for_status()
            audio_data = response.content

        content_type = response.headers.get("content-type", "audio/wav")
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        return json.dumps({"audio_base64": audio_b64, "content_type": content_type, "run_id": run_id})

    @kernel_function(description="Create a custom voice clone from an audio sample using camb.ai", name="clone_voice")
    async def clone_voice(
        self,
        voice_name: Annotated[str, "Name for the cloned voice."],
        audio_file_path: Annotated[str, "Path to the audio file to clone from."],
        gender: Annotated[int, "Gender of the voice (1=male, 2=female)."],
        description: Annotated[str | None, "Optional description of the voice."] = None,
        age: Annotated[int | None, "Optional age of the voice."] = None,
    ) -> str:
        """Create a custom voice clone from an audio sample.

        Args:
            voice_name: Name for the cloned voice.
            audio_file_path: Path to the audio file.
            gender: Gender (1=male, 2=female).
            description: Optional description.
            age: Optional age.

        Returns:
            JSON string with voice_id, voice_name, and status.
        """
        kwargs: dict[str, Any] = {
            "voice_name": voice_name,
            "gender": gender,
        }
        if description is not None:
            kwargs["description"] = description
        if age is not None:
            kwargs["age"] = age

        with open(audio_file_path, "rb") as f:
            kwargs["file"] = f
            result = await self.async_client.voice_cloning.create_custom_voice(**kwargs)

        return json.dumps({
            "voice_id": getattr(result, "voice_id", None) or getattr(result, "id", None),
            "voice_name": getattr(result, "voice_name", None) or getattr(result, "name", None),
            "status": getattr(result, "status", "created"),
        })

    @kernel_function(description="List available voices from camb.ai", name="list_voices")
    async def list_voices(self) -> str:
        """List all available voices.

        Returns:
            JSON array of voice objects with id, name, gender, age, and language.
        """
        result = await self.async_client.voice_cloning.list_voices()

        voices = []
        for voice in result:
            if isinstance(voice, dict):
                voices.append({
                    "id": voice.get("id"),
                    "name": voice.get("voice_name"),
                    "gender": voice.get("gender"),
                    "age": voice.get("age"),
                    "language": voice.get("language"),
                })
            else:
                voices.append({
                    "id": getattr(voice, "id", None),
                    "name": getattr(voice, "voice_name", None) or getattr(voice, "name", None),
                    "gender": getattr(voice, "gender", None),
                    "age": getattr(voice, "age", None),
                    "language": getattr(voice, "language", None),
                })

        return json.dumps(voices)

    @kernel_function(
        description="Generate sounds or music from a text description using camb.ai", name="text_to_sound"
    )
    async def text_to_sound(
        self,
        prompt: Annotated[str, "Text description of the sound or music to generate."],
        duration: Annotated[float | None, "Duration in seconds (optional)."] = None,
        audio_type: Annotated[str | None, "Type of audio: 'music' or 'sound' (optional)."] = None,
    ) -> str:
        """Generate sounds or music from a text description.

        Args:
            prompt: Description of the sound/music to generate.
            duration: Optional duration in seconds.
            audio_type: Optional type ("music" or "sound").

        Returns:
            JSON string with base64-encoded audio.
        """
        kwargs: dict[str, Any] = {"prompt": prompt}
        if duration is not None:
            kwargs["duration"] = duration
        if audio_type is not None:
            kwargs["audio_type"] = audio_type

        task_result = await self.async_client.text_to_audio.create_text_to_audio(**kwargs)

        run_id = await self._poll_task_status(
            self.async_client.text_to_audio.get_text_to_audio_status,
            task_result.task_id,
        )

        # Collect streaming audio result
        audio_chunks: list[bytes] = []
        async for chunk in self.async_client.text_to_audio.get_text_to_audio_result(run_id):
            audio_chunks.append(chunk)

        audio_data = b"".join(audio_chunks)
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        return json.dumps({"audio_base64": audio_b64, "run_id": run_id})

    @kernel_function(
        description="Separate audio into vocals and background tracks using camb.ai", name="separate_audio"
    )
    async def separate_audio(
        self,
        audio_file_path: Annotated[str, "Path to the audio file to separate."],
    ) -> str:
        """Separate audio into vocals and background tracks.

        Args:
            audio_file_path: Path to the audio file.

        Returns:
            JSON string with vocals_url and background_url.
        """
        with open(audio_file_path, "rb") as f:
            task_result = await self.async_client.audio_separation.create_audio_separation(media_file=f)

        run_id = await self._poll_task_status(
            self.async_client.audio_separation.get_audio_separation_status,
            task_result.task_id,
        )

        result = await self.async_client.audio_separation.get_audio_separation_run_info(run_id)

        return json.dumps({
            "vocals_url": getattr(result, "vocals_url", None),
            "background_url": getattr(result, "background_url", None),
            "run_id": run_id,
        })
