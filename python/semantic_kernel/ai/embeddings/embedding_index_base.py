# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List, Tuple

from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord


class EmbeddingIndexBase(ABC):
    @abstractmethod
    async def get_nearest_matches_async(
        self,
        collection: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
    ) -> List[Tuple[MemoryRecord, float]]:
        pass
