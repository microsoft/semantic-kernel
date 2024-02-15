# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from numpy import ndarray


class EmbeddingGeneratorBase(ABC):
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> "ndarray":
        pass
