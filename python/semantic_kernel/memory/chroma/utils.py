from typing import TYPE_CHECKING, List

from numpy import array, linalg, ndarray
from semantic_kernel.memory.memory_record import MemoryRecord

if TYPE_CHECKING:
    from chromadb.api.types import QueryResult


def camel_to_snake(camel_str):
    snake_str = camel_str[0].lower()
    for char in camel_str[1:]:
        if char.isupper():
            snake_str += "_" + char.lower()
        else:
            snake_str += char
    return snake_str


def query_results_to_records(results: "QueryResult") -> List[MemoryRecord]:
    memory_records = [
        (
            MemoryRecord(
                is_reference=metadata["is_reference"],
                external_source_name=metadata["external_source_name"],
                id=id,
                description=metadata["description"],
                text=document,
                # TODO: get_async say embedding is optional but Record constructor requires it
                embedding=embedding,
                # TODO: what is key for?
                key=None,
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
