# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.kernel_extensions.extends_kernel import ExtendsKernel
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory


class MemoryConfiguration(ExtendsKernel):
    def use_memory(
        self,
        storage: MemoryStoreBase,
        embeddings_generator: Optional[EmbeddingGeneratorBase] = None,
    ) -> None:
        kernel = self.kernel()

        if embeddings_generator is None:
            backend_label = kernel.config.get_embedding_backend_service_id()
            if not backend_label:
                raise ValueError(
                    "The embedding backend label cannot be `None` or empty"
                )

            embeddings_backend = kernel.config.get_ai_backend(
                EmbeddingGeneratorBase, backend_label
            )
            if not embeddings_backend:
                raise ValueError(f"AI configuration is missing for: {backend_label}")

            embeddings_generator = embeddings_backend(kernel)

        if storage is None:
            raise ValueError("The storage instance provided cannot be `None`")
        if embeddings_generator is None:
            raise ValueError("The embedding generator cannot be `None`")

        kernel.register_memory(SemanticTextMemory(storage, embeddings_generator))
