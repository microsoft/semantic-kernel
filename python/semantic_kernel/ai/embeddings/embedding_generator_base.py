# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List

from numpy import ndarray


class EmbeddingGeneratorBase(ABC):
    @abstractmethod
    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        pass
