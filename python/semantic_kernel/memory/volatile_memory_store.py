# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple, Dict
from copy import deepcopy

from numpy import array, linalg, ndarray

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


class VolatileMemoryStore(MemoryStoreBase):
    _store: Dict[str, Dict[str, MemoryRecord]]
    _logger: Logger

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self._store = {}
        self._logger = logger or NullLogger()
        
    async def create_collection_async(
        self,
        collection_name: str
        # TODO: cancel token
    ) -> None:
        if collection_name in self._store:
            pass
        else:
            self._store[collection_name] = {}

    async def get_collections_async(
        self        
        # TODO: cancel token
    ) -> List[str]:
        return list(self._store.keys())

    async def delete_collection_async(
        self,
        collection_name: str
        # TODO: cancel token
    ) -> None:
        if collection_name in self._store:
            del self._store[collection_name]

    async def does_collection_exist_async(
        self,
        collection_name: str
        # TODO: cancel token
    ) -> bool:
        return collection_name in self._store

    async def upsert_async(
        self,
        collection_name: str,
        record: MemoryRecord
        # TODO: cancel token
    ) -> str:
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        record._key = record._id
        self._store[collection_name][record._key] = record
        return record._key

    async def upsert_batch_async(
        self,
        collection_name: str,
        records: List[MemoryRecord]
        # TODO: cancel token
    ) -> List[str]:
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        for record in records:
            record._key = record._id
            self._store[collection_name][record._key] = record
        return [record._key for record in records]

    async def get_async(
        self,
        collection_name: str,
        key: str,
        with_embedding: bool = False
        # TODO: cancel token
    ) -> MemoryRecord:
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        if key not in self._store[collection_name]:
            raise Exception(f"Key '{key}' not found in collection '{collection_name}'")

        result = self._store[collection_name][key]

        if not with_embedding:
            # create copy of results without embeddings
            result = deepcopy(result)
            result._embedding = None
        return result

    async def get_batch_async(
        self,
        collection_name: str,
        keys: List[str],
        with_embeddings: bool = False
        # TODO: cancel token
    ) -> List[MemoryRecord]:
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        results = [self._store[collection_name][key] for key in keys if key in self._store[collection_name]]

        if not with_embeddings:
            # create copy of results without embeddings
            for result in results:
                result = deepcopy(result)
                result._embedding = None
        return results

    async def remove_async(
        self,
        collection_name: str,
        key: str
        # TODO: cancel token
    ) -> None:
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        if key not in self._store[collection_name]:
            raise Exception(f"Key '{key}' not found in collection '{collection_name}'")

        del self._store[collection_name][key]

    async def remove_batch_async(
        self,
        collection_name: str,
        keys: List[str]
        # TODO: cancel token
    ) -> None:
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        for key in keys:
            if key in self._store[collection_name]:
                del self._store[collection_name][key]
    
    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False
        # TODO: cancel token
    ) -> Tuple[MemoryRecord, float]:
        return self.get_nearest_matches_async(collection_name=collection_name, embedding=embedding, limit=1, min_relevance_score=min_relevance_score, with_embeddings=with_embedding)

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
        # TODO: cancel token
    ) -> List[Tuple[MemoryRecord, float]]:
        if collection_name not in self._store:
            return []
        
        # Get all the records in the collection
        memory_records = list(self._store[collection_name].values())

        # Convert the collection of embeddings into a numpy array (stacked)
        embeddings = array([x._embedding for x in memory_records], dtype=float)
        embeddings = embeddings.reshape(embeddings.shape[0], -1)

        # If the query embedding has shape (1, embedding_size),
        # reshape it to (embedding_size,)
        if len(embedding.shape) == 2:
            embedding = embedding.reshape(
                embedding.shape[1],
            )

        # Use numpy to get the cosine similarity between the query
        # embedding and all the embeddings in the collection
        similarity_scores = self.compute_similarity_scores(embedding, embeddings)

        # Then, sort the results by the similarity score
        sorted_results = sorted(
            zip(memory_records, similarity_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        # Then, filter out the results that are below the minimum relevance score
        filtered_results = [x for x in sorted_results if x[1] >= min_relevance_score]

        # Then, take the top N results
        top_results = filtered_results[:limit]

        if not with_embeddings:
            # create copy of results without embeddings
            for result in top_results:
                result = deepcopy(result)
                result[0]._embedding = None
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
