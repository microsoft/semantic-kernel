# Copyright (c) Microsoft. All rights reserved.

from numpy import ndarray

from semantic_kernel.memory.storage.memory_storage_base import MemoryStorageBase


class VolatileMemoryStore(MemoryStorageBase):
    def get_nearest_matches_async(
        self,
        collection: str,
        embedding: ndarray,
        limit: int = 1,
        min_relevance_score: float = 0.7,
    ):
        pass
