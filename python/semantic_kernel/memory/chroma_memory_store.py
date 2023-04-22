# Copyright (c) Microsoft. All rights reserved.

"""
3 cases

Case 1) use semantic kernel's default compute similarity function
Case 2) use chroma's nearest neighbor search
Case 3) use custom similarity function


"""

import inspect
from logging import Logger
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple, Union

from numpy import array, linalg, ndarray
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.storage.chroma_data_store import ChromaDataStore
from semantic_kernel.utils.null_logger import NullLogger

if TYPE_CHECKING:
    import chromadb.config

AvailableComputeSimilarityFunction = Union[str, Callable[[ndarray, ndarray], ndarray]]
DEFAULT_COMPUTE_SIMILARITY_FUNCTIONS = ["sk-default", "chroma"]


def validate_similarity_function(func) -> bool:
    if func in DEFAULT_COMPUTE_SIMILARITY_FUNCTIONS:
        return True
    else:
        # validate typing for custom compute_similarity function
        # Callable[[ndarray, ndarray], ndarray]
        param_a = inspect.Parameter(
            "a", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=ndarray
        )
        param_b = inspect.Parameter(
            "b", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=ndarray
        )
        expected_signature = inspect.Signature(
            [param_a, param_b], return_annotation=ndarray
        )
        function_signature = inspect.signature(func)

        return function_signature == expected_signature


class ChromaMemoryStore(ChromaDataStore, MemoryStoreBase):
    def __init__(
        self,
        logger: Optional[Logger] = None,
        similarity_fetch_limit: int = 5,
        similarity_compute_func: AvailableComputeSimilarityFunction = "sk-default",
        persist_directory: Optional[str] = None,
        client_settings: Optional["chromadb.config.Settings"] = None,
    ) -> None:
        assert validate_similarity_function(similarity_compute_func)
        self._similarity_compute_func = similarity_compute_func
        self._similarity_fetch_limit = similarity_fetch_limit

        super().__init__(
            persist_directory=persist_directory, client_settings=client_settings
        )
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
            n_results=self._similarity_fetch_limit,
            include=["embeddings", "metadatas", "documents", "distances"],
        )

        # Convert the collection of embeddings into a numpy array (stacked)
        embedding_array = array(query_results["embeddings"][0])
        embedding_array = embedding_array.reshape(embedding_array.shape[0], -1)

        # If the query embedding has shape (1, embedding_size),
        # reshape it to (embedding_size,)
        if len(embedding.shape) == 2:
            embedding = embedding.reshape(
                embedding.shape[1],
            )

        # Compute similarity scores
        if self._similarity_compute_func == "sk-default":
            # Case 1) use semantic kernel's default compute similarity function
            similarity_score = self.compute_similarity_scores(
                embedding, embedding_array
            )
        elif self._similarity_compute_func == "chroma":
            # Case 2) use chroma's default distance
            similarity_score = query_results["distances"][0]
        else:
            # Case 3) use custom similarity function
            similarity_score = self._similarity_compute_func(embedding, embedding_array)

        # Convert query results into memory records
        record_list = [
            (record, distance)
            for record, distance in zip(
                self.query_results_to_memory_records(query_results),
                similarity_score,
            )
        ]

        if self._similarity_compute_func == "chroma":
            # default chroma uses distance as similarity score (lower is better)
            filtered_results = [x for x in record_list if x[1] <= min_relevance_score]
            top_results = filtered_results[:limit]
        else:
            sorted_results = sorted(
                record_list,
                key=lambda x: x[1],
                reverse=True,
            )

            filtered_results = [
                x for x in sorted_results if x[1] >= min_relevance_score
            ]
            top_results = filtered_results[:limit]

        return top_results

    def compute_similarity_scores(
        self, embedding: ndarray, embedding_array: ndarray
    ) -> ndarray:
        """
        Semantic kernel's default compute similarity function.
        (Code from VolatileMemoryStore)

        Compute the similarity scores between the
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
