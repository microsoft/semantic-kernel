# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping
from typing import Any, TypeVar

from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import OpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_to_image_base import OpenAITextToImageBase
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

T_ = TypeVar("T_", bound="OpenAITextToImage")


class OpenAITextToImage(OpenAIConfigBase, OpenAITextToImageBase):
    """OpenAI Text to Image service."""

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
        """Initializes a new instance of the OpenAITextToImage class.

        Args:
            ai_model_id: OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id: Service ID tied to the execution settings.
            api_key: The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id: The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client: An existing client to use. (Optional)
            env_file_path: Use the environment settings file as
                a fallback to environment variables. (Optional)
            env_file_encoding: The encoding of the environment settings file. (Optional)
        """
        try:
            openai_settings = OpenAISettings(
                api_key=api_key,
                org_id=org_id,
                text_to_image_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create OpenAI settings.", ex) from ex
        if not openai_settings.text_to_image_model_id:
            raise ServiceInitializationError("The OpenAI text to image model ID is required.")
        super().__init__(
            ai_model_id=openai_settings.text_to_image_model_id,
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            ai_model_type=OpenAIModelTypes.TEXT_TO_IMAGE,
            org_id=openai_settings.org_id,
            service_id=service_id,
            default_headers=default_headers,
            client=async_client,
        )

    @classmethod
    def from_dict(cls: type[T_], settings: dict[str, Any]) -> T_:
        """Initialize an Open AI service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
        """
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            org_id=settings.get("org_id"),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers", {}),
            env_file_path=settings.get("env_file_path"),
        )
