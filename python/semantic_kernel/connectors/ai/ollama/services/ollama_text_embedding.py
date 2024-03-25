# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging

import aiohttp
from numpy import array, ndarray
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession

logger: logging.Logger = logging.getLogger(__name__)


class OllamaTextEmbedding(EmbeddingGeneratorBase):
    """Ollama embeddings client.

    Make sure to have the ollama service running either locally or remotely.

    Arguments:
        ai_model_id {str} -- Ollama model name, see https://ollama.ai/library
        url {str | HttpUrl | None} -- URL of the Ollama server, defaults to http://localhost:11434/api/embeddings
        session {aiohttp.ClientSession | None} -- Optional client session to use for requests.
    """

    url: HttpUrl = "http://localhost:11434/api/embeddings"
    session: aiohttp.ClientSession | None = None

    async def generate_embeddings(self, texts: list[str], **kwargs) -> ndarray:
        """
        Generates embeddings for a list of texts.

        Arguments:
            texts {list[str]} -- Texts to generate embeddings for.

        Returns:
            ndarray -- Embeddings for the texts.
        """
        result = []
        for text in texts:
            async with AsyncSession(self.session) as session:
                async with session.post(
                    self.url,
                    json={"model": self.ai_model_id, "prompt": text, "options": kwargs},
                ) as response:
                    response.raise_for_status()
                    response = await response.json()
                    result.append(response["embedding"])
        return array(result)
