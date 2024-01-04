# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import List, Optional

import aiohttp
from numpy import array, ndarray
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class OllamaTextEmbedding(EmbeddingGeneratorBase, AIServiceClientBase):
    url: HttpUrl = "http://localhost:11434/api/embeddings"
    session: Optional[aiohttp.ClientSession] = None

    async def generate_embeddings_async(self, texts: List[str], **kwargs) -> ndarray:
        """
        Generates embeddings for a list of texts.

        Arguments:
            texts {List[str]} -- Texts to generate embeddings for.

        Returns:
            ndarray -- Embeddings for the texts.
        """
        if self.session:
            async with self.session.post(
                self.url, json={"model": self.ai_model_id, "texts": texts, "options": kwargs}
            ) as response:
                response.raise_for_status()
                return array(await response.json())
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url, json={"model": self.ai_model_id, "texts": texts, "options": kwargs}
            ) as response:
                response.raise_for_status()
                return array(await response.json())
