# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping

from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import OpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_realtime_base import (
    OpenAIRealtimeBase,
    OpenAIRealtimeWebRTCBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


class OpenAIRealtime(OpenAIRealtimeBase, OpenAIConfigBase):
    """OpenAI Realtime service."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OpenAITextCompletion service.

        Args:
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not openai_settings.text_model_id:
            raise ServiceInitializationError("The OpenAI text model ID is required.")
        super().__init__(
            ai_model_id=openai_settings.text_model_id,
            service_id=service_id,
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            org_id=openai_settings.org_id,
            ai_model_type=OpenAIModelTypes.TEXT,
            default_headers=default_headers,
            client=async_client,
        )


class OpenAIRealtimeWebRTC(OpenAIRealtimeWebRTCBase, OpenAIConfigBase):
    """OpenAI Realtime service."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OpenAITextCompletion service.

        Args:
            ai_model_id (str | None): OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id (str | None): The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                text_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not openai_settings.text_model_id:
            raise ServiceInitializationError("The OpenAI text model ID is required.")
        super().__init__(
            ai_model_id=openai_settings.text_model_id,
            service_id=service_id,
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            org_id=openai_settings.org_id,
            ai_model_type=OpenAIModelTypes.TEXT,
            default_headers=default_headers,
            client=async_client,
        )
