# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Dict, Optional

from semantic_kernel.connectors.ai.open_ai.services.open_ai_config_base import (
    OpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding_base import (
    OpenAITextEmbeddingBase,
)


class OpenAITextEmbedding(OpenAIConfigBase, OpenAITextEmbeddingBase):
    """OpenAI Text Embedding class."""

    def __init__(
        self,
        ai_model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
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
        """
        super().__init__(
            ai_model_id=ai_model_id,
            api_key=api_key,
            ai_model_type=OpenAIModelTypes.EMBEDDING,
            org_id=org_id,
            log=log,
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
            log=settings.get("log"),
        )
