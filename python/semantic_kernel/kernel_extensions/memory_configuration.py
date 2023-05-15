# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
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
            service_id = kernel.get_text_embedding_generation_service_id()
            if not service_id:
                raise ValueError("The embedding service id cannot be `None` or empty")

            embeddings_service = kernel.get_ai_service(
                EmbeddingGeneratorBase, service_id
            )
            if not embeddings_service:
                raise ValueError(f"AI configuration is missing for: {service_id}")

            embeddings_generator = embeddings_service(kernel)

        if storage is None:
            raise ValueError("The storage instance provided cannot be `None`")
        if embeddings_generator is None:
            raise ValueError("The embedding generator cannot be `None`")

        kernel.register_memory(SemanticTextMemory(storage, embeddings_generator))
