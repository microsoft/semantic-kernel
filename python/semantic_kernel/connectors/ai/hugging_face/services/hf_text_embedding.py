# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

import sentence_transformers
import torch
from numpy import array, ndarray

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class HuggingFaceTextEmbedding(EmbeddingGeneratorBase):
    device: str
    generator: Any

    def __init__(
        self,
        ai_model_id: str,
        device: int | None = -1,
        service_id: str | None = None,
    ) -> None:
        """Initializes a new instance of the HuggingFaceTextEmbedding class.

        Args:
            ai_model_id (str): Hugging Face model card string, see
                https://huggingface.co/sentence-transformers
            device (Optional[int]): Device to run the model on, -1 for CPU, 0+ for GPU.
            service_id (Optional[str]): Service ID for the model.

        Note that this model will be downloaded from the Hugging Face model hub.
        """
        resolved_device = f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"
        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id,
            device=resolved_device,
            generator=sentence_transformers.SentenceTransformer(model_name_or_path=ai_model_id, device=resolved_device),
        )

    @override
    async def generate_embeddings(self, texts: list[str], **kwargs: Any) -> ndarray:
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.generator.encode(texts, **kwargs)
            return array(embeddings)
        except Exception as e:
            raise ServiceResponseException("Hugging Face embeddings failed", e) from e
