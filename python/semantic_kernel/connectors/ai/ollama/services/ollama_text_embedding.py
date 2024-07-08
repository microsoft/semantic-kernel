# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any

from ollama import AsyncClient

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from numpy import array, ndarray

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OllamaTextEmbedding(EmbeddingGeneratorBase):
    """Ollama embeddings client.

    Make sure to have the ollama service running either locally or remotely.
    """

    @override
    async def generate_embeddings(self, texts: list[str], **kwargs: Any) -> ndarray:
        result = []
        for text in texts:
            response_object = await AsyncClient().embeddings(model=self.ai_model_id, prompt=text)
            result.append(response_object["embedding"])

        return array(result)
