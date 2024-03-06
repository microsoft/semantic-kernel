# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from numpy import ndarray


class EmbeddingGeneratorBase(AIServiceClientBase, ABC):
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> "ndarray":
        pass
