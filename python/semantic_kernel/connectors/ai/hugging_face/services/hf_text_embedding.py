# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional

from numpy import array, ndarray

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class HuggingFaceTextEmbedding(EmbeddingGeneratorBase):
    _model_id: str
    _device: int
    _log: Logger

    def __init__(
        self,
        model_id: str,
        device: Optional[int] = -1,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initializes a new instance of the HuggingFaceTextEmbedding class.

        Arguments:
            model_id {str} -- Hugging Face model card string, see
                https://huggingface.co/sentence-transformers
            device {Optional[int]} -- Device to run the model on, -1 for CPU, 0+ for GPU.
            log {Optional[Logger]} -- Logger instance.

        Note that this model will be downloaded from the Hugging Face model hub.
        """
        self._model_id = model_id
        self._log = log if log is not None else NullLogger()

        try:
            import sentence_transformers
            import torch
        except ImportError:
            raise ImportError(
                "Please ensure that torch and sentence-transformers are installed to use HuggingFaceTextEmbedding"
            )

        self.device = (
            "cuda:" + str(device)
            if device >= 0 and torch.cuda.is_available()
            else "cpu"
        )
        self.generator = sentence_transformers.SentenceTransformer(
            model_name_or_path=self._model_id, device=self.device
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
            self._log.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.generator.encode(texts)
            return array(embeddings)
        except Exception as e:
            raise AIException("Hugging Face embeddings failed", e)
