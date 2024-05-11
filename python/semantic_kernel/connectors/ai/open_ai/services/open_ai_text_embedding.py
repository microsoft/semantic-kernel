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
from semantic_kernel.connectors.ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextEmbedding(OpenAIConfigBase, OpenAITextEmbeddingBase):
    """OpenAI Text Embedding class."""

    def __init__(
        self,
        ai_model_id: str,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        use_env_settings_file: bool = False,
    ) -> None:
        """
        Initializes a new instance of the OpenAITextCompletion class.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            default_headers {Optional[Mapping[str,str]]}: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
            use_env_settings_file {bool} -- Use the environment settings file as
                a fallback to environment variables. (Optional)
        """
        try:
            openai_settings = OpenAISettings.create(use_env_settings_file=True)
        except ValidationError as e:
            logger.error(f"Error loading OpenAI settings: {e}")
            raise ServiceInitializationError("Error loading OpenAI settings") from e

        api_key = openai_settings.api_key.get_secret_value()
        org_id = openai_settings.org_id

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
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
            use_env_settings_file=settings.get("use_env_settings_file", False),
        )
