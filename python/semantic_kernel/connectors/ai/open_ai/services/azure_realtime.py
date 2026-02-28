# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
import warnings
from collections.abc import Callable, Coroutine, Mapping
from typing import TYPE_CHECKING, Any

from aiohttp import ClientSession
from azure.core.credentials import TokenCredential
from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from openai.resources.realtime.realtime import AsyncRealtimeConnection
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    AzureRealtimeExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import (
    OpenAIRealtimeWebRTCBase,
    OpenAIRealtimeWebsocketBase,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from aiortc.mediastreams import MediaStreamTrack
    from numpy import ndarray

    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger("semantic_kernel.connectors.ai.open_ai.realtime")


@experimental
class AzureRealtimeWebsocket(OpenAIRealtimeWebsocketBase, AzureOpenAIConfigBase):
    """Azure OpenAI Realtime service using WebSocket protocol."""

    def __init__(
        self,
        audio_output_callback: Callable[["ndarray"], Coroutine[Any, Any, None]] | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: AsyncAzureADTokenProvider | None = None,
        token_endpoint: str | None = None,
        websocket_base_url: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        credential: TokenCredential | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an AzureRealtimeWebsocket service.

        Args:
            audio_output_callback: The audio output callback, optional.
                This should be a coroutine, that takes a ndarray with audio as input.
                The goal of this function is to allow you to play the audio with the
                least amount of latency possible, because it is called first before further processing.
                It can also be set in the `receive` method.
                Even when passed, the audio content will still be
                added to the receiving queue.
            service_id: The service ID for the Azure deployment. (Optional)
            api_key: The optional api key. If provided, will override the value in the
                env vars or .env file.
            deployment_name: The optional deployment. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
            endpoint: The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url: The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version: The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token: The Azure Active Directory token. (Optional)
            ad_token_provider: The Azure Active Directory token provider. (Optional)
            token_endpoint: The token endpoint to request an Azure token. (Optional)
            websocket_base_url: The base URL for the WebSocket connection. (Optional)
                If not provided, the default URL will be used.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client: An existing client to use. (Optional)
            env_file_path: Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding: The encoding of the environment settings file. (Optional)
            credential: The credential to use for authentication. (Optional)
            kwargs: Additional arguments.
                This can include:
                kernel (Kernel): the kernel to use for function calls
                plugins (list[object] or dict[str, object]): the plugins to use for function calls
                settings (OpenAIRealtimeExecutionSettings): the settings to use for the session
                chat_history (ChatHistory): the chat history to use for the session
                Otherwise they can also be passed to the context manager.
        """
        try:
            azure_openai_settings = AzureOpenAISettings(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                realtime_deployment_name=deployment_name,
                api_version=api_version,
                token_endpoint=token_endpoint,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not azure_openai_settings.realtime_deployment_name:
            raise ServiceInitializationError("The OpenAI realtime model ID is required.")
        super().__init__(
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
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
            websocket_base_url=websocket_base_url,
            credential=credential,
            **kwargs,
        )

    @override
    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        return AzureRealtimeExecutionSettings

    @override
    async def create_session(
        self,
        chat_history: "ChatHistory | None" = None,
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> None:
        """Create a session in the service.

        The Azure GA Realtime endpoint (/openai/v1/realtime) does not accept
        the api-version query parameter. The openai SDK always adds it, so we
        bypass the SDK's _configure_realtime and build the connection directly.
        """
        from websockets.asyncio.client import connect as ws_connect

        # Build the GA WebSocket URL: wss://<resource>.openai.azure.com/openai/v1/realtime?model=<deployment-name>
        # Note: GA uses ?model= (not ?deployment= which was preview)
        # See: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-websockets
        endpoint = str(self.client._base_url).rstrip("/")  # type: ignore[attr-defined]
        if "/openai" in endpoint:
            endpoint = endpoint[: endpoint.index("/openai")]
        url = f"wss://{endpoint.split('://')[-1]}/openai/v1/realtime?model={self.ai_model_id}"

        # Build auth headers
        auth_headers: dict[str, str] = {}
        if self.client.api_key and self.client.api_key != "<missing API key>":
            auth_headers["api-key"] = self.client.api_key
        else:
            token = await self.client._get_azure_ad_token()  # type: ignore[attr-defined]
            if token:
                auth_headers["Authorization"] = f"Bearer {token}"

        ws = await ws_connect(
            url,
            additional_headers={
                **auth_headers,
                USER_AGENT: SEMANTIC_KERNEL_USER_AGENT,
            },
        )

        self.connection = AsyncRealtimeConnection(ws)
        self.connected.set()
        await self.update_session(settings=settings, chat_history=chat_history, **kwargs)


@experimental
class AzureRealtimeWebRTC(OpenAIRealtimeWebRTCBase, AzureOpenAIConfigBase):
    """Azure OpenAI Realtime service using WebRTC protocol."""

    def __init__(
        self,
        audio_track: "MediaStreamTrack",
        region: str | None = None,
        audio_output_callback: Callable[["ndarray"], Coroutine[Any, Any, None]] | None = None,
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
        credential: TokenCredential | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an AzureRealtimeWebRTC service.

        Args:
            audio_track: The audio track to use for the service, only used by WebRTC.
                It can be any class that implements the AudioStreamTrack interface.
            region: Deprecated. No longer needed for GA Realtime API.
                Previously required for the preview WebRTC endpoint.
            audio_output_callback: The audio output callback, optional.
                This should be a coroutine, that takes a ndarray with audio as input.
                The goal of this function is to allow you to play the audio with the
                least amount of latency possible, because it is called first before further processing.
                It can also be set in the `receive` method.
                Even when passed, the audio content will still be
                added to the receiving queue.
            service_id: The service ID for the Azure deployment. (Optional)
            api_key: The optional api key. If provided, will override the value in the
                env vars or .env file.
            deployment_name: The optional deployment. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
            endpoint: The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url: The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version: The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token: The Azure Active Directory token. (Optional)
            ad_token_provider: The Azure Active Directory token provider. (Optional)
            token_endpoint: The token endpoint to request an Azure token. (Optional)
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client: An existing client to use. (Optional)
            env_file_path: Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding: The encoding of the environment settings file. (Optional)
            credential: The credential to use for authentication. (Optional)
            kwargs: Additional arguments.
                This can include:
                kernel (Kernel): the kernel to use for function calls
                plugins (list[object] or dict[str, object]): the plugins to use for function calls
                settings (OpenAIRealtimeExecutionSettings): the settings to use for the session
                chat_history (ChatHistory): the chat history to use for the session
                Otherwise they can also be passed to the context manager.
        """
        try:
            azure_openai_settings = AzureOpenAISettings(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                realtime_deployment_name=deployment_name,
                api_version=api_version,
                token_endpoint=token_endpoint,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not azure_openai_settings.realtime_deployment_name:
            raise ServiceInitializationError("The OpenAI realtime model ID is required.")
        if region is not None:
            warnings.warn(
                "The 'region' parameter is deprecated and no longer needed for the GA Realtime API. "
                "The WebRTC endpoint is now derived from the resource endpoint.",
                DeprecationWarning,
                stacklevel=2,
            )
        if audio_track:
            kwargs["audio_track"] = audio_track
        super().__init__(
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
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
            credential=credential,
            **kwargs,
        )

    @override
    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        return AzureRealtimeExecutionSettings

    @override
    def _get_ephemeral_token_headers_and_url(self) -> tuple[dict[str, str], str]:
        """Get the headers and URL for the ephemeral token.

        Uses the GA endpoint format: POST /openai/v1/realtime/client_secrets
        See: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-webrtc
        """
        endpoint = str(self.client._base_url).rstrip("/")  # type: ignore[attr-defined]
        # Strip any trailing path segments to get the base Azure resource URL
        # base_url typically looks like https://<resource>.openai.azure.com/openai/...
        # We need: https://<resource>.openai.azure.com/openai/v1/realtime/client_secrets
        if "/openai" in endpoint:
            endpoint = endpoint[: endpoint.index("/openai")]
        url = f"{endpoint}/openai/v1/realtime/client_secrets"

        if self.client.api_key and self.client.api_key != "<missing API key>":
            return (
                {
                    "api-key": self.client.api_key,
                    "Content-Type": "application/json",
                },
                url,
            )
        if self.client._azure_ad_token is not None:  # type: ignore[attr-defined]
            return (
                {
                    "Authorization": f"Bearer {self.client._azure_ad_token}",  # type: ignore[attr-defined]
                    "Content-Type": "application/json",
                },
                url,
            )
        raise ServiceInitializationError("No API key or Azure AD token available for ephemeral token request.")

    @override
    async def _get_ephemeral_token(self) -> str:
        """Get an ephemeral token from Azure OpenAI.

        Azure GA requires a nested session object:
            {"session": {"type": "realtime", "model": "<deployment>"}}
        And returns the token directly as {"value": "..."} rather than
        OpenAI's {"client_secret": {"value": "..."}}.
        See: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-webrtc
        """
        data = {
            "session": {
                "type": "realtime",
                "model": self.ai_model_id,
            }
        }
        headers, url = self._get_ephemeral_token_headers_and_url()
        headers = prepend_semantic_kernel_to_user_agent(headers)
        try:
            async with (
                ClientSession() as session,
                session.post(url, headers=headers, json=data) as response,
            ):
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"Failed to get ephemeral token: {error_text}")

                result = await response.json()
                # Azure GA format returns {"value": "token"} directly
                return result["value"]

        except Exception as e:
            logger.error(f"Failed to get ephemeral token: {e!s}")
            raise

    @override
    def _get_webrtc_url(self) -> str:
        """Get the WebRTC URL.

        Uses the GA endpoint format: /openai/v1/realtime/calls
        See: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio-webrtc
        """
        endpoint = str(self.client._base_url).rstrip("/")  # type: ignore[attr-defined]
        if "/openai" in endpoint:
            endpoint = endpoint[: endpoint.index("/openai")]
        return f"{endpoint}/openai/v1/realtime/calls"
