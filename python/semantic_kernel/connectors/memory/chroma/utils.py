# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, List

from numpy import array, linalg, ndarray

from semantic_kernel.memory.memory_record import MemoryRecord

if TYPE_CHECKING:
    from chromadb.api.types import QueryResult


def camel_to_snake(camel_str):
    snake_str = ""
    for i, char in enumerate(camel_str):
        if char.isupper():
            if i != 0 and camel_str[i - 1].islower():
                snake_str += "_"
            if i != len(camel_str) - 1 and camel_str[i + 1].islower():
                snake_str += "_"
        snake_str += char.lower()
    return snake_str


def query_results_to_records(
    results: "QueryResult", with_embedding: bool
) -> List[MemoryRecord]:
    # if results has only one record, it will be a list instead of a nested list
    # this is to make sure that results is always a nested list
    # {'ids': ['test_id1'], 'embeddings': [[...]], 'documents': ['sample text1'], 'metadatas': [{...}]}
    # => {'ids': [['test_id1']], 'embeddings': [[[...]]], 'documents': [['sample text1']], 'metadatas': [[{...}]]}
    try:
        if isinstance(results["ids"][0], str):
            for k, v in results.items():
                results[k] = [v]
    except IndexError:
        return []

    if with_embedding:
        memory_records = [
            (
                MemoryRecord(
                    is_reference=(metadata["is_reference"] == "True"),
                    external_source_name=metadata["external_source_name"],
                    id=metadata["id"],
                    description=metadata["description"],
                    text=document,
                    embedding=embedding,
                    additional_metadata=metadata["additional_metadata"],
                    key=id,
                    timestamp=metadata["timestamp"],
                )
            )
            for id, document, embedding, metadata in zip(
                results["ids"][0],
                results["documents"][0],
                results["embeddings"][0],
                results["metadatas"][0],
            )
        ]
    else:
        memory_records = [
            (
                MemoryRecord(
                    is_reference=(metadata["is_reference"] == "True"),
                    external_source_name=metadata["external_source_name"],
                    id=metadata["id"],
                    description=metadata["description"],
                    text=document,
                    embedding=None,
                    additional_metadata=metadata["additional_metadata"],
                    key=id,
                    timestamp=metadata["timestamp"],
                )
            )
            for id, document, metadata in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
            )
        ]
    return memory_records


def chroma_compute_similarity_scores(
    embedding: ndarray, embedding_array: ndarray, logger=None
) -> ndarray:
    """Computes the cosine similarity scores between a query embedding and a group of embeddings.
    Arguments:
        embedding {ndarray} -- The query embedding.
        embedding_array {ndarray} -- The group of embeddings.
    Returns:
        ndarray -- The cosine similarity scores.
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
        if not valid_indices.all() and logger:
            logger.warning(
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
