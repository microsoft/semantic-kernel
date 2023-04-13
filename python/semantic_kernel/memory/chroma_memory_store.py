# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Callable, List, Optional, Tuple

from numpy import ndarray
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.storage.chroma_data_store import ChromaDataStore
from semantic_kernel.utils.null_logger import NullLogger

ComputeSimilarityFuncType = Callable[[ndarray, ndarray], ndarray]


class ChromaMemoryStore(ChromaDataStore, MemoryStoreBase):
    def __init__(
        self,
        logger: Optional[Logger] = None,
        compute_similarity_fetch_limit: int = 10,
        compute_similarity_scores_func: ComputeSimilarityFuncType = None,
    ) -> None:
        super().__init__()
        self._logger = logger or NullLogger()
        self._compute_similarity_fetch_limit = compute_similarity_fetch_limit
        self._compute_similarity_scores_func = compute_similarity_scores_func

    async def get_nearest_matches_async(
        self,
        collection: str,
        embedding: ndarray,
        limit: int = 1,
        min_relevance_score: float = 0.7,
    ) -> List[Tuple[MemoryRecord, float]]:
        collection = await self.get_collection_async(collection)
        if collection is None:
            return []

        # use Chroma nearest neighbor search if no similarity function is provided
        if self._compute_similarity_scores_func is None:
            query_results = collection.query(
                query_embeddings=embedding.tolist(),
                n_results=limit,
                include=["embeddings", "metadatas", "documents", "distances"],
            )
        else:
            query_results = collection.get(
                include=["embeddings", "metadatas", "documents"],
            )
            # dimension compatibility with Chroma's query results
            query_results["ids"] = [query_results["ids"]]
            query_results["documents"] = [query_results["documents"]]
            query_results["metadatas"] = [query_results["metadatas"]]

            # compute similarity scores using the custom function
            query_results["distances"] = self._compute_similarity_scores_func(
                embedding, query_results["embeddings"]
            )

        # Convert Chroma query results into a list of MemoryRecords
        record_list = [
            (record, distance)
            for record, distance in zip(
                self.query_results_to_memory_records(query_results),
                query_results["distances"][0],
            )
        ]

        if self._compute_similarity_scores_func is not None:
            # Then, sort the results by the similarity score
            sorted_results = sorted(
                record_list,
                key=lambda x: x[1],
                reverse=True,
            )

            filtered_results = [
                x for x in sorted_results if x[1] >= min_relevance_score
            ]
            top_results = filtered_results[:limit]
        else:
            top_results = record_list[:limit]

        return top_results
