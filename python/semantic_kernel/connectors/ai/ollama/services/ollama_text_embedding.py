# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import aiohttp
from numpy import array, ndarray
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OllamaTextEmbedding(EmbeddingGeneratorBase):
    """Ollama embeddings client.

    Make sure to have the ollama service running either locally or remotely.

    Args:
        ai_model_id (str): Ollama model name, see https://ollama.ai/library
        url (Optional[Union[str, HttpUrl]]): URL of the Ollama server, defaults to http://localhost:11434/api/embeddings
        session (Optional[aiohttp.ClientSession]): Optional client session to use for requests.
    """

    url: HttpUrl = "http://localhost:11434/api/embeddings"
    session: aiohttp.ClientSession | None = None

    @override
    async def generate_embeddings(self, texts: list[str], **kwargs: Any) -> ndarray:
        result = []
        for text in texts:
            async with (
                AsyncSession(self.session) as session,
                session.post(
                    self.url,
                    json={"model": self.ai_model_id, "prompt": text, "options": kwargs},
                ) as response,
            ):
                response.raise_for_status()
                response = await response.json()
                result.append(response["embedding"])
        return array(result)
