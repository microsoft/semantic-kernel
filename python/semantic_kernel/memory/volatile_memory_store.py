# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple

from numpy import array, linalg, ndarray

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.storage.volatile_data_store import VolatileDataStore
from semantic_kernel.utils.null_logger import NullLogger


class VolatileMemoryStore(VolatileDataStore, MemoryStoreBase):
    def __init__(self, logger: Optional[Logger] = None) -> None:
        super().__init__()
        self._logger = logger or NullLogger()

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

        # If the query embedding has shape (1, embedding_size),
        # reshape it to (embedding_size,)
        if len(embedding.shape) == 2:
            embedding = embedding.reshape(
                embedding.shape[1],
            )

        # Use numpy to get the cosine similarity between the query
        # embedding and all the embeddings in the collection
        similarity_scores = self.compute_similarity_scores(embedding, embedding_array)

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

    def compute_similarity_scores(
        self, embedding: ndarray, embedding_array: ndarray
    ) -> ndarray:
        """Compute the similarity scores between the
        query embedding and all the embeddings in the collection.
        Ignore the corresponding operation if zero vectors
        are involved (in query embedding or the embedding collection)

        :param embedding: The query embedding.
        :param embedding_array: The collection of embeddings.
        :return: similarity_scores: The similarity scores between the query embedding
            and all the embeddings in the collection.
        """

        query_norm = linalg.norm(embedding)
        collection_norm = linalg.norm(embedding_array, axis=1)

        # Compute indices for which the similarity scores can be computed
        valid_indices = (query_norm != 0) & (collection_norm != 0)

        # Initialize the similarity scores with -1 to distinguish the cases
        # between zero similarity from orthogonal vectors and invalid similarity
        similarity_scores = array([-1.0] * embedding_array.shape[0])

        if valid_indices.any():
            similarity_scores[valid_indices] = embedding.dot(
                embedding_array[valid_indices].T
            ) / (query_norm * collection_norm[valid_indices])
            if not valid_indices.all():
                self._logger.warning(
                    "Some vectors in the embedding collection are zero vectors."
                    "Ignoring cosine similarity score computation for those vectors."
                )
        else:
            raise ValueError(
                f"Invalid vectors, cannot compute cosine similarity scores"
                f"for zero vectors"
                f"{embedding_array} or {embedding}"
            )
        return similarity_scores
