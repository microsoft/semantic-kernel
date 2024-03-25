# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from numpy import ndarray


class EmbeddingGeneratorBase(AIServiceClientBase, ABC):
    @abstractmethod
    async def generate_embeddings(self, texts: list[str]) -> "ndarray":
        pass
