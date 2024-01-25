# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, List, Optional

import sentence_transformers
import torch
from numpy import array, ndarray

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class HuggingFaceTextEmbedding(EmbeddingGeneratorBase, AIServiceClientBase):
    device: str
    generator: Any

    def __init__(
        self,
        ai_model_id: str,
        device: Optional[int] = -1,
        log: Optional[Any] = None,
    ) -> None:
        """
        Initializes a new instance of the HuggingFaceTextEmbedding class.

        Arguments:
            ai_model_id {str} -- Hugging Face model card string, see
                https://huggingface.co/sentence-transformers
            device {Optional[int]} -- Device to run the model on, -1 for CPU, 0+ for GPU.
            log  -- The logger instance to use. (Optional) (Deprecated)

        Note that this model will be downloaded from the Hugging Face model hub.
        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        resolved_device = f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"
        super().__init__(
            ai_model_id=ai_model_id,
            device=resolved_device,
            generator=sentence_transformers.SentenceTransformer(model_name_or_path=ai_model_id, device=resolved_device),
        )

    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        """
        Generates embeddings for a list of texts.

        Arguments:
            texts {List[str]} -- Texts to generate embeddings for.

        Returns:
            ndarray -- Embeddings for the texts.
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.generator.encode(texts)
            return array(embeddings)
        except Exception as e:
            raise AIException("Hugging Face embeddings failed", e)
