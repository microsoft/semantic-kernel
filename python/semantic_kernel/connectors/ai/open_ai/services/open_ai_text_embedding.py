# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional

from numpy import ndarray

from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_service_calls import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)


class OpenAITextEmbedding(OpenAITextCompletion, EmbeddingGeneratorBase):
    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initializes a new instance of the OpenAITextCompletion class.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
        """
        super().__init__(
            model_id=model_id,
            api_key=api_key,
            org_id=org_id,
            log=log,
        )
        self.model_type = OpenAIModelTypes.EMBEDDING

    async def generate_embeddings_async(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        return await self._send_embedding_request(texts, batch_size)

    async def complete_stream_async(
        self,
        prompt: str,
        settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        raise NotImplementedError(
            "Embedding class does not currently support completions"
        )

    async def complete_async(
        self,
        prompt: str,
        settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        raise NotImplementedError(
            "Embedding class does not currently support completions"
        )
