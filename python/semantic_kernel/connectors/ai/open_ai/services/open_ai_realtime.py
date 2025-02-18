# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable, Coroutine, Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar

from numpy import ndarray
from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import OpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_base import OpenAIRealtimeBase
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_webrtc import OpenAIRealtimeWebRTCBase
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_websocket import (
    OpenAIRealtimeWebsocketBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from aiortc.mediastreams import MediaStreamTrack


_T = TypeVar("_T", bound="OpenAIRealtime")


__all__ = ["OpenAIRealtime"]


@experimental_class
class OpenAIRealtime(OpenAIRealtimeBase):
    """OpenAI Realtime service."""

    def __new__(cls: type["_T"], protocol: Literal["websocket", "webrtc"], *args: Any, **kwargs: Any) -> "_T":
        """Pick the right subclass, based on protocol."""
        subclass_map = {subcl.protocol: subcl for subcl in cls.__subclasses__()}
        subclass = subclass_map[protocol]
        return super(OpenAIRealtime, subclass).__new__(subclass)

    def __init__(
        self,
        protocol: Literal["websocket", "webrtc"],
        *,
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
        audio_track: "MediaStreamTrack | None" = None,
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
            protocol: The protocol to use, must be either "websocket" or "webrtc".
            audio_output_callback: The audio output callback, optional.
                This should be a coroutine, that takes a ndarray with audio as input.
                The goal of this function is to allow you to play the audio with the
                least amount of latency possible.
                It is called first in both websockets and webrtc.
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
        """
        try:
            openai_settings = OpenAISettings.create(
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
            protocol=protocol,
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


@experimental_class
class OpenAIRealtimeWebRTC(OpenAIRealtime, OpenAIRealtimeWebRTCBase, OpenAIConfigBase):
    """OpenAI Realtime service using WebRTC protocol.

    This should not be used directly, use OpenAIRealtime instead.
    Set protocol="webrtc" to use this class.
    """

    protocol: ClassVar[Literal["webrtc"]] = "webrtc"

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize an OpenAIRealtime service using WebRTC protocol."""
        super().__init__(
            *args,
            **kwargs,
        )


@experimental_class
class OpenAIRealtimeWebSocket(OpenAIRealtime, OpenAIRealtimeWebsocketBase, OpenAIConfigBase):
    """OpenAI Realtime service using WebSocket protocol.

    This should not be used directly, use OpenAIRealtime instead.
    Set protocol="websocket" to use this class.
    """

    protocol: ClassVar[Literal["websocket"]] = "websocket"

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )
