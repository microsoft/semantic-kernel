from unittest.mock import AsyncMock, MagicMock

import numpy as np
from numpy import ndarray
from pytest import approx, fixture, mark, raises

from semantic_kernel.memory import ChromaMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord


@fixture
def store():
    return ChromaMemoryStore()


@fixture
def mock_collection():
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["a", "b"]],
        "embeddings": [[np.array([0.5, 0.5]), np.array([0.25, 0.75])]],
        "metadatas": [
            [
                {
                    "is_reference": False,
                    "external_source_name": "test",
                    "description": "test",
                },
                {
                    "is_reference": False,
                    "external_source_name": "test",
                    "description": "test",
                },
            ]
        ],
        "documents": [["doc-1", "doc-2"]],
        "distances": [[0.9, 0.6]],
    }
    return mock_collection


def test_init_default():
    store = ChromaMemoryStore()
    assert store._similarity_compute_func == "sk-default"


def test_init_custom_similarity_fetch_limit():
    store = ChromaMemoryStore(similarity_fetch_limit=15)
    assert store._similarity_fetch_limit == 15


def test_init_custom_similarity_compute_func_str():
    store = ChromaMemoryStore(similarity_compute_func="chroma")
    assert store._similarity_compute_func == "chroma"


def test_init_custom_similarity_compute_func_callable():
    def custom_similarity_func(a: ndarray, b: ndarray) -> ndarray:
        return a * b

    store = ChromaMemoryStore(similarity_compute_func=custom_similarity_func)
    assert store._similarity_compute_func == custom_similarity_func


def test_init_invalid_similarity_compute_func():
    def invalid_similarity_func(a: int, b: int) -> int:
        return a + b

    with raises(AssertionError):
        ChromaMemoryStore(similarity_compute_func=invalid_similarity_func)


@mark.asyncio
async def test_get_nearest_matches_async_sk_default_similarity(store, mock_collection):
    store.get_collection_async = AsyncMock(return_value=mock_collection)

    results = await store.get_nearest_matches_async(
        "collection_name", np.array([0.5, 0.5]), limit=1
    )

    assert len(results) == 1
    assert isinstance(results[0][0], MemoryRecord)
    assert results[0][1] == approx(1, abs=1e-5)


@mark.asyncio
async def test_get_nearest_matches_async_chroma_similarity(store, mock_collection):
    store.get_collection_async = AsyncMock(return_value=mock_collection)
    store._similarity_compute_func = "chroma"

    results = await store.get_nearest_matches_async(
        "collection_name", np.array([0.5, 0.5]), limit=1
    )

    assert len(results) == 1
    assert isinstance(results[0][0], MemoryRecord)
    assert results[0][1] == 0.6


@mark.asyncio
async def test_get_nearest_matches_async_custom_similarity(store, mock_collection):
    custom_similarity_func = MagicMock(return_value=[0.9, 0.8])
    store.get_collection_async = AsyncMock(return_value=mock_collection)
    store._similarity_compute_func = custom_similarity_func

    results = await store.get_nearest_matches_async(
        "collection_name", np.array([0.5, 0.5]), limit=1
    )

    assert len(results) == 1
    assert isinstance(results[0][0], MemoryRecord)
    assert results[0][1] == 0.9


@mark.asyncio
async def test_cosine_similarity_valid():
    """Test the cosine similarity computation"""
    chroma_memory_store = ChromaMemoryStore()
    # Test case 1: Two valid embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[1, 0, 1], [0, 1, 0]])
    expected_scores = np.array([1.0, 0.0])
    scores = chroma_memory_store.compute_similarity_scores(
        embedding=query_embedding, embedding_array=collection_embeddings
    )
    # using allclose instead of equality because
    # of floating point rounding errors
    np.testing.assert_allclose(scores, expected_scores)


@mark.asyncio
async def test_cosine_similarity_zero_query():
    chroma_memory_store = ChromaMemoryStore()
    # Test case 2: Zero vector as query_embedding
    query_embedding = np.array([0, 0, 0])
    collection_embeddings = np.array([[1, 0, 1], [0, 1, 0]])
    with raises(ValueError):
        _ = chroma_memory_store.compute_similarity_scores(
            query_embedding, collection_embeddings
        )


@mark.asyncio
async def test_cosine_similarity_zero_collection():
    chroma_memory_store = ChromaMemoryStore()
    # Test case 3: Zero vector as collection_embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[0, 0, 0], [0, 0, 0]])
    with raises(ValueError):
        _ = chroma_memory_store.compute_similarity_scores(
            query_embedding, collection_embeddings
        )


@mark.asyncio
async def test_cosine_similarity_partial_zero_collection():
    chroma_memory_store = ChromaMemoryStore()
    # Test case 4: Partial zero vector as collection_embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[1, 0, 1], [0, 0, 0]])
    expected_scores = np.array([1.0, -1.0])
    scores = chroma_memory_store.compute_similarity_scores(
        query_embedding, collection_embeddings
    )
    assert np.allclose(expected_scores, scores)
