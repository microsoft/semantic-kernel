# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple

from numpy import ndarray
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.storage.chroma_data_store import ChromaDataStore
from semantic_kernel.utils.null_logger import NullLogger


class ChromaMemoryStore(ChromaDataStore, MemoryStoreBase):
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
        collection = await self.get_collection_async(collection)
        if collection is None:
            return []

        query_results = collection.query(
            query_embeddings=embedding.tolist(),
            n_results=limit,
            include=["embeddings", "metadatas", "documents", "distances"],
        )

        output_list = [
            (record, distance)
            for record, distance in zip(
                self.query_results_to_memory_records(query_results),
                query_results["distances"][0],
            )
        ]

        return output_list

    # TODO: Need to decide semantic-kernel will use chroma's similarity score or not
    # def compute_similarity_scores(
    #     self, embedding: ndarray, embedding_array: ndarray
    # ) -> ndarray:
    #     pass
