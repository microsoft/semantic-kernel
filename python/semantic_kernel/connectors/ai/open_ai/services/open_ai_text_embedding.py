# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Dict, Mapping, Optional, overload

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding_base import (
    OpenAITextEmbeddingBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextEmbedding(OpenAIConfigBase, OpenAITextEmbeddingBase):
    """OpenAI Text Embedding class."""

    @overload
    def __init__(
        self,
        ai_model_id: str,
        async_client: AsyncOpenAI,
        service_id: Optional[str] = None,
    ) -> None:
        """
        Initialize an OpenAITextEmbedding service.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            async_client {AsyncOpenAI} -- An existing client to use.
        """

    def __init__(
        self,
        ai_model_id: str,
        api_key: Optional[str] = None,
        org_id: Optional[str] = None,
        service_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
    ) -> None:
        """
        Initializes a new instance of the OpenAITextCompletion class.

        Arguments:
            ai_model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            default_headers {Optional[Mapping[str,str]]}: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncOpenAI]} -- An existing client to use. (Optional)
        """
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
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
        )
