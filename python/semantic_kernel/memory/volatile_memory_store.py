# Copyright (c) Microsoft. All rights reserved.

from typing import List, Tuple

from numpy import array, linalg, ndarray

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.storage.volatile_data_store import VolatileDataStore


class VolatileMemoryStore(VolatileDataStore, MemoryStoreBase):
    def __init__(self) -> None:
        super().__init__()

    async def get_nearest_matches_async(
        self,
        collection: str,
        embedding: ndarray,
        limit: int = 1,
        min_relevance_score: float = 0.7,
    ) -> List[Tuple[MemoryRecord, float]]:
        if collection not in self._store:
            return []

        embedding_collection = list([x.value for x in self._store[collection].values()])
        # Convert the collection of embeddings into a numpy array (stacked)
        embedding_array = array(
            [x.embedding for x in embedding_collection], dtype=float
        )
        embedding_array = embedding_array.reshape(embedding_array.shape[0], -1)

        # Use numpy to get the cosine similarity between the query
        # embedding and all the embeddings in the collection
        similarity_scores = (
            embedding.dot(embedding_array.T)
            / (linalg.norm(embedding) * linalg.norm(embedding_array, axis=1))
        )[0]

        # Then, sort the results by the similarity score
        sorted_results = sorted(
            zip(embedding_collection, similarity_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        # Then, filter out the results that are below the minimum relevance score
        filtered_results = [x for x in sorted_results if x[1] >= min_relevance_score]

        # Then, take the top N results
        top_results = filtered_results[:limit]
        return top_results
