# Copyright (c) Microsoft. All rights reserved.

import base64
import binascii
from collections.abc import Mapping
from typing import Any, TypeVar

import aiohttp
from pydantic import ValidationError

from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_text_to_audio_execution_settings import (
    MiniMaxTextToAudioExecutionSettings,
)
from semantic_kernel.connectors.ai.minimax.settings.minimax_settings import MiniMaxSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_to_audio_client_base import TextToAudioClientBase
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException

T_ = TypeVar("T_", bound="MiniMaxTextToAudio")


class MiniMaxTextToAudio(TextToAudioClientBase):
    """MiniMax speech-2.x text-to-audio HTTP service."""

    api_key: str
    base_url: str
    default_headers: dict[str, str]

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        service_id: str | None = None,
        base_url: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize a MiniMax text-to-audio client."""
        try:
            settings = MiniMaxSettings(
                api_key=api_key,
                text_to_audio_model_id=ai_model_id,
                text_to_audio_base_url=base_url,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create MiniMax settings.", ex) from ex
        if not settings.text_to_audio_model_id:
            raise ServiceInitializationError("The MiniMax text to audio model ID is required.")
        super().__init__(
            ai_model_id=settings.text_to_audio_model_id,
            service_id=service_id or settings.text_to_audio_model_id,
            api_key=settings.api_key.get_secret_value(),
            base_url=settings.text_to_audio_base_url,
            default_headers=dict(default_headers or {}),
        )

    @classmethod
    def from_dict(cls: type[T_], settings: dict[str, Any]) -> T_:
        """Initialize a client from a settings dictionary."""
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            service_id=settings.get("service_id"),
            base_url=settings.get("base_url"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
        )

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Return the request settings type accepted by this client."""
        return MiniMaxTextToAudioExecutionSettings

    def service_url(self) -> str:
        """Return the configured MiniMax speech endpoint."""
        return self.base_url

    async def get_audio_contents(
        self,
        text: str,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[AudioContent]:
        """Convert text into audio using MiniMax's regional HTTP endpoint."""
        if settings is None:
            request = MiniMaxTextToAudioExecutionSettings(ai_model_id=self.ai_model_id)
        elif isinstance(settings, MiniMaxTextToAudioExecutionSettings):
            request = settings
        else:
            request = self.get_prompt_execution_settings_from_settings(settings)
        request.ai_model_id = request.ai_model_id or self.ai_model_id
        request.input = text
        payload = request.prepare_settings_dict()
        payload.update(kwargs)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=120)
            async with (
                aiohttp.ClientSession(timeout=timeout, headers=headers) as session,
                session.post(self.base_url, json=payload) as response,
            ):
                body = await response.json(content_type=None)
                response.raise_for_status()
            if body.get("base_resp", {}).get("status_code") not in (None, 0):
                raise RuntimeError(body.get("base_resp", {}).get("status_msg", "MiniMax request failed"))
            encoded = body.get("data", {}).get("audio")
            if not encoded:
                raise RuntimeError("MiniMax response did not contain audio data")
            try:
                audio = bytes.fromhex(encoded)
            except (ValueError, TypeError, binascii.Error):
                audio = base64.b64decode(encoded)
            return [AudioContent(ai_model_id=request.ai_model_id, data=audio, data_format="base64", inner_content=body)]
        except Exception as ex:
            raise ServiceResponseException(f"{type(self)} service failed to generate audio", ex) from ex
