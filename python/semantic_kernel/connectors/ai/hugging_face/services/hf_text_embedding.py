# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import sentence_transformers
import torch
from numpy import ndarray

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
<<<<<<< main
=======
from semantic_kernel.connectors.ai.ai_exception import AIException
>>>>>>> ms/small_fixes
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from torch import Tensor

    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )

logger: logging.Logger = logging.getLogger(__name__)


<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
@experimental_class
class HuggingFaceTextEmbedding(EmbeddingGeneratorBase):
    """Hugging Face text embedding service."""

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
class HuggingFaceTextEmbedding(EmbeddingGeneratorBase):
>>>>>>> ms/small_fixes
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
class HuggingFaceTextEmbedding(EmbeddingGeneratorBase):
>>>>>>> ms/small_fixes
>>>>>>> origin/main
    device: str
    generator: Any

    def __init__(
        self,
        ai_model_id: str,
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        device: int = -1,
        service_id: str | None = None,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        device: int = -1,
        service_id: str | None = None,
=======
=======
>>>>>>> origin/main
<<<<<<< main
        device: int = -1,
        service_id: str | None = None,
=======
        device: Optional[int] = -1,
        service_id: Optional[str] = None,
>>>>>>> ms/small_fixes
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    ) -> None:
        """Initializes a new instance of the HuggingFaceTextEmbedding class.

        Args:
            ai_model_id (str): Hugging Face model card string, see
                https://huggingface.co/sentence-transformers
            device (int): Device to run the model on, -1 for CPU, 0+ for GPU. (optional)
            service_id (str): Service ID for the model. (optional)

        Note that this model will be downloaded from the Hugging Face model hub.
        """
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        resolved_device = (
            f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"
        )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
<<<<<<< main
        resolved_device = (
            f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"
        )
=======
        resolved_device = f"cuda:{device}" if device >= 0 and torch.cuda.is_available() else "cpu"
>>>>>>> ms/small_fixes
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id,
            device=resolved_device,
            generator=sentence_transformers.SentenceTransformer(
                model_name_or_path=ai_model_id, device=resolved_device
            ),
        )

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts.")
            return self.generator.encode(
                sentences=texts, convert_to_numpy=True, **kwargs
            )
        except Exception as e:
            raise ServiceResponseException("Hugging Face embeddings failed", e) from e

    @override
    async def generate_raw_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> "list[Tensor] | ndarray | Tensor":
        try:
            logger.info(f"Generating raw embeddings for {len(texts)} texts.")
            return self.generator.encode(sentences=texts, **kwargs)
        except Exception as e:
            raise ServiceResponseException("Hugging Face embeddings failed", e) from e
