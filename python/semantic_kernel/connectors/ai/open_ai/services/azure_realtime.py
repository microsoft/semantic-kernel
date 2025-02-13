# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable, Coroutine, Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar

from numpy import ndarray
from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_base import OpenAIRealtimeBase
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_webrtc import OpenAIRealtimeWebRTCBase
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_websocket import (
    OpenAIRealtimeWebsocketBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if TYPE_CHECKING:
    from aiortc.mediastreams import MediaStreamTrack


_T = TypeVar("_T", bound="AzureRealtime")


__all__ = ["AzureRealtime"]


class AzureRealtime(OpenAIRealtimeBase):
    """Azure OpenAI Realtime service."""

    def __new__(cls: type["_T"], protocol: str, *args: Any, **kwargs: Any) -> "_T":
        """Pick the right subclass, based on protocol."""
        subclass_map = {subcl.protocol: subcl for subcl in cls.__subclasses__()}
        subclass = subclass_map[protocol]
        return super(AzureRealtime, subclass).__new__(subclass)

    def __init__(
        self,
        protocol: Literal["websocket", "webrtc"],
        *,
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
        audio_track: "MediaStreamTrack | None" = None,
        service_id: str | None = None,
        api_key: str | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: AsyncAzureADTokenProvider | None = None,
        token_endpoint: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
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
            service_id (str | None): The service ID for the Azure deployment. (Optional)
            api_key  (str | None): The optional api key. If provided, will override the value in the
                env vars or .env file.
            deployment_name  (str | None): The optional deployment. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
            endpoint (str | None): The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url (str | None): The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version (str | None): The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token (str | None): The Azure Active Directory token. (Optional)
            ad_token_provider (AsyncAzureADTokenProvider): The Azure Active Directory token provider. (Optional)
            token_endpoint (str | None): The token endpoint to request an Azure token. (Optional)
            default_headers (Mapping[str, str]): The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (AsyncAzureOpenAI | None): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
            kwargs: Additional arguments.
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                realtime_model_id=deployment_name,
                api_version=api_version,
                token_endpoint=token_endpoint,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not azure_openai_settings.realtime_deployment_name:
            raise ServiceInitializationError("The OpenAI realtime model ID is required.")
        if audio_track:
            kwargs["audio_track"] = audio_track
        super().__init__(
            protocol=protocol,
            audio_output_callback=audio_output_callback,
            deployment_name=azure_openai_settings.realtime_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            token_endpoint=azure_openai_settings.token_endpoint,
            ai_model_type=OpenAIModelTypes.REALTIME,
            service_id=service_id,
            default_headers=default_headers,
            client=async_client,
            **kwargs,
        )


class AzureRealtimeWebRTC(AzureRealtime, OpenAIRealtimeWebRTCBase, AzureOpenAIConfigBase):
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
        raise NotImplementedError("Azure Realtime WebRTC is not yet supported.")


class AzureRealtimeWebsocket(AzureRealtime, OpenAIRealtimeWebsocketBase, AzureOpenAIConfigBase):
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
