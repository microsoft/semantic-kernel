# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.ai.open_ai.services.open_ai_text_embedding import (
    OpenAITextEmbedding,
)
from semantic_kernel.configuration.backend_types import BackendType
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory


def use_memory(
    kernel: KernelBase,
    storage: MemoryStoreBase,
    embeddings_generator: Optional[EmbeddingGeneratorBase] = None,
) -> None:
    if embeddings_generator is None:
        backend_label = kernel.config.default_embeddings_backend
        Verify.not_empty(backend_label, "The embedding backend label is empty")

        embeddings_backend_config = kernel.config.get_embeddings_backend(backend_label)
        Verify.not_null(
            embeddings_backend_config,
            f"AI configuration is missing for: {backend_label}",
        )

        if embeddings_backend_config.backend_type == BackendType.OpenAI:
            assert embeddings_backend_config.open_ai is not None  # for mypy
            embeddings_generator = OpenAITextEmbedding(
                embeddings_backend_config.open_ai.model_id,
                embeddings_backend_config.open_ai.api_key,
                embeddings_backend_config.open_ai.org_id,
                kernel.logger,
            )
        else:
            # TODO: this
            raise NotImplementedError(
                f"Embeddings backend {embeddings_backend_config.backend_type} "
                "is not yet implemented"
            )

    Verify.not_null(storage, "The storage instance provided is None")
    Verify.not_null(embeddings_generator, "The embedding generator is None")

    kernel.register_memory(SemanticTextMemory(storage, embeddings_generator))
