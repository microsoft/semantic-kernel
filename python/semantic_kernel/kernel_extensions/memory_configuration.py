# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
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
        backend_label = kernel.config.get_embedding_backend_service_id()
        Verify.not_empty(backend_label, "The embedding backend label is empty")

        embeddings_backend = kernel.config.get_ai_backend(
            EmbeddingGeneratorBase, backend_label
        )
        Verify.not_null(
            embeddings_backend,
            f"AI configuration is missing for: {backend_label}",
        )

        embeddings_generator = embeddings_backend(kernel)

    Verify.not_null(storage, "The storage instance provided is None")
    Verify.not_null(embeddings_generator, "The embedding generator is None")

    kernel.register_memory(SemanticTextMemory(storage, embeddings_generator))
