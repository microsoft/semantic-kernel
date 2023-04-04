import numpy as np
from pytest import mark, raises

from semantic_kernel.memory import VolatileMemoryStore


@mark.asyncio
async def test_cosine_similarity_valid():
    """Test the cosine similarity computation"""
    volatile_memory_store = VolatileMemoryStore()
    # Test case 1: Two valid embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[1, 0, 1], [0, 1, 0]])
    expected_scores = np.array([1.0, 0.0])
    scores = volatile_memory_store.compute_similarity_scores(
        embedding=query_embedding, embedding_array=collection_embeddings
    )
    # using allclose instead of equality because
    # of floating point rounding errors
    np.testing.assert_allclose(scores, expected_scores)


@mark.asyncio
async def test_cosine_similarity_zero_query():
    volatile_memory_store = VolatileMemoryStore()
    # Test case 2: Zero vector as query_embedding
    query_embedding = np.array([0, 0, 0])
    collection_embeddings = np.array([[1, 0, 1], [0, 1, 0]])
    with raises(ValueError):
        _ = volatile_memory_store.compute_similarity_scores(
            query_embedding, collection_embeddings
        )


@mark.asyncio
async def test_cosine_similarity_zero_collection():
    volatile_memory_store = VolatileMemoryStore()
    # Test case 3: Zero vector as collection_embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[0, 0, 0], [0, 0, 0]])
    with raises(ValueError):
        _ = volatile_memory_store.compute_similarity_scores(
            query_embedding, collection_embeddings
        )


@mark.asyncio
async def test_cosine_similarity_partial_zero_collection():
    volatile_memory_store = VolatileMemoryStore()
    # Test case 4: Partial zero vector as collection_embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[1, 0, 1], [0, 0, 0]])
    expected_scores = np.array([1.0, -1.0])
    scores = volatile_memory_store.compute_similarity_scores(
        query_embedding, collection_embeddings
    )
    assert np.allclose(expected_scores, scores)
