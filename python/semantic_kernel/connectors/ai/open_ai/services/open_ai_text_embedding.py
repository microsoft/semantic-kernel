# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Dict, Mapping, Optional

from openai import AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding_base import (
    OpenAITextEmbeddingBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAITextEmbedding(OpenAIConfigBase, OpenAITextEmbeddingBase):
    """OpenAI Text Embedding class."""

    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        org_id: str | None = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        env_file_path: str | None = None,
    ) -> None:
        """
        Initializes a new instance of the OpenAITextCompletion class.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            service_id {str | None} -- Service ID tied to the execution settings.
            api_key {str | None} -- The optional API key to use. If provided will override,
                the env vars or .env file value.
            org_id {str | None} -- The optional org ID to use. If provided will override,
                the env vars or .env file value.
            default_headers {Optional[Mapping[str,str]]}: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            env_file_path {str | None} -- Use the environment settings file as
                a fallback to environment variables. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(env_file_path=env_file_path)
        except ValidationError as e:
            logger.warning(f"Failed to load OpenAI pydantic settings: {e}")

        api_key = api_key or (
            openai_settings.api_key.get_secret_value() if openai_settings and openai_settings.api_key else None
        )
        org_id = org_id or (openai_settings.org_id if openai_settings and openai_settings.org_id else None)
        ai_model_id = ai_model_id or (
            openai_settings.embedding_model_id if openai_settings and openai_settings.embedding_model_id else None
        )

        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            ai_model_type=OpenAIModelTypes.EMBEDDING,
            org_id=org_id,
            service_id=service_id,
            default_headers=default_headers,
            async_client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAITextEmbedding":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAITextEmbedding(
            ai_model_id=settings["ai_model_id"],
            api_key=settings.get("api_key", None),
            org_id=settings.get("org_id", None),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path", None),
        )
