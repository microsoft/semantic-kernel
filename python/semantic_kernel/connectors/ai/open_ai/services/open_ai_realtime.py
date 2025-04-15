# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable, Coroutine, Mapping
from typing import TYPE_CHECKING, Any

from aiortc import (
    MediaStreamTrack,
)
from numpy import ndarray
from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import (
    ListenEvents,
    OpenAIRealtimeWebRTCBase,
    OpenAIRealtimeWebsocketBase,
    SendEvents,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import OpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from aiortc.mediastreams import MediaStreamTrack


logger: logging.Logger = logging.getLogger(__name__)

__all__ = [
    "ListenEvents",
    "OpenAIRealtimeWebRTC",
    "OpenAIRealtimeWebsocket",
    "SendEvents",
]


@experimental
class OpenAIRealtimeWebRTC(OpenAIRealtimeWebRTCBase, OpenAIConfigBase):
    """OpenAI Realtime service using WebRTC protocol."""

    def __init__(
        self,
        audio_track: "MediaStreamTrack",
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIRealtime service.

        Args:
            audio_output_callback: The audio output callback, optional.
                This should be a coroutine, that takes a ndarray with audio as input.
                The goal of this function is to allow you to play the audio with the
                least amount of latency possible, because it is called first before further processing.
                It can also be set in the `receive` method.
                Even when passed, the audio content will still be
                added to the receiving queue.
            audio_track: The audio track to use for the service, only used by WebRTC.
                A default is supplied if not provided.
                It can be any class that implements the AudioStreamTrack interface.
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
            kwargs: Additional arguments.
                This can include:
                kernel (Kernel): the kernel to use for function calls
                plugins (list[object] or dict[str, object]): the plugins to use for function calls
                settings (OpenAIRealtimeExecutionSettings): the settings to use for the session
                chat_history (ChatHistory): the chat history to use for the session
                Otherwise they can also be passed to the context manager.
        """
        try:
            openai_settings = OpenAISettings(
                api_key=api_key,
                org_id=org_id,
                realtime_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not openai_settings.realtime_model_id:
            raise ServiceInitializationError("The OpenAI realtime model ID is required.")
        if audio_track:
            kwargs["audio_track"] = audio_track
        super().__init__(
            audio_output_callback=audio_output_callback,
            ai_model_id=openai_settings.realtime_model_id,
            service_id=service_id,
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            org_id=openai_settings.org_id,
            ai_model_type=OpenAIModelTypes.REALTIME,
            default_headers=default_headers,
            client=client,
            **kwargs,
        )


# region Websocket


@experimental
class OpenAIRealtimeWebsocket(OpenAIRealtimeWebsocketBase, OpenAIConfigBase):
    """OpenAI Realtime service using WebSocket protocol."""

    def __init__(
        self,
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIRealtime service.

        Args:
            audio_output_callback: The audio output callback, optional.
                This should be a coroutine, that takes a ndarray with audio as input.
                The goal of this function is to allow you to play the audio with the
                least amount of latency possible, because it is called first before further processing.
                It can also be set in the `receive` method.
                Even when passed, the audio content will still be
                added to the receiving queue.
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
            kwargs: Additional arguments.
            kwargs: Additional arguments.
                This can include:
                kernel (Kernel): the kernel to use for function calls
                plugins (list[object] or dict[str, object]): the plugins to use for function calls
                settings (OpenAIRealtimeExecutionSettings): the settings to use for the session
                chat_history (ChatHistory): the chat history to use for the session
                Otherwise they can also be passed to the context manager.
        """
        try:
            openai_settings = OpenAISettings(
                api_key=api_key,
                org_id=org_id,
                realtime_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not openai_settings.realtime_model_id:
            raise ServiceInitializationError("The OpenAI realtime model ID is required.")
        super().__init__(
            audio_output_callback=audio_output_callback,
            ai_model_id=openai_settings.realtime_model_id,
            service_id=service_id,
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            org_id=openai_settings.org_id,
            ai_model_type=OpenAIModelTypes.REALTIME,
            default_headers=default_headers,
            client=client,
            **kwargs,
        )
