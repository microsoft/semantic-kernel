# Copyright (c) Microsoft. All rights reserved.

from numpy import ndarray
from abc import ABC, abstractmethod
from typing import List, Any


class EmbeddingGeneratorBase(ABC):
    @abstractmethod
    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        pass
