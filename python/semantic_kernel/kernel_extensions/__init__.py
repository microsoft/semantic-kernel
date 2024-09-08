# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, List, Optional

from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_extensions.inline_function_definitions import (
    create_semantic_function,
)
from semantic_kernel.kernel_extensions.memory_configuration import use_memory
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class KernelExtensions:
    @staticmethod
    def create_semantic_function(
        kernel: KernelBase,
        prompt_template: str,
        function_name: Optional[str] = None,
        skill_name: Optional[str] = None,
        description: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.0,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
    ) -> "SKFunctionBase":
        return create_semantic_function(
            kernel,
            prompt_template,
            function_name,
            skill_name,
            description,
            max_tokens,
            temperature,
            top_p,
            presence_penalty,
            frequency_penalty,
            stop_sequences,
        )

    @staticmethod
    def use_memory(
        kernel: KernelBase,
        storage: MemoryStoreBase,
        embeddings_generator: Optional[EmbeddingGeneratorBase] = None,
    ) -> None:
        use_memory(kernel, storage, embeddings_generator)
