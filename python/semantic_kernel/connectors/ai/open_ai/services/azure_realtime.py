# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Callable, Coroutine, Mapping
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from numpy import ndarray
from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    AzureRealtimeExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import OpenAIRealtimeWebsocketBase
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureRealtimeWebsocket(OpenAIRealtimeWebsocketBase, AzureOpenAIConfigBase):
    """Azure OpenAI Realtime service using WebSocket protocol."""

    def __init__(
        self,
        audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None,
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
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client: An existing client to use. (Optional)
            env_file_path: Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding: The encoding of the environment settings file. (Optional)
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
            **kwargs,
        )

    @override
    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        return AzureRealtimeExecutionSettings
