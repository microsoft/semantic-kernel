from semantic_kernel.memory import VolatileMemoryStore
import numpy as np
from unittest import TestCase


def test_cosine_similarity_valid():
    """Test the cosine similarity computation"""
    # Test case 1: Two valid embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[1, 0, 1], [0, 1, 0]])
    expected_scores = np.array([1.0, 0.0])
    scores = await VolatileMemoryStore.compute_similarity_scores(query_embedding, collection_embeddings)
    assert scores == expected_scores


def test_cosine_similarity_zero_query():
    # Test case 2: Zero vector as query_embedding
    query_embedding = np.array([0, 0, 0])
    collection_embeddings = np.array([[1, 0, 1], [0, 1, 0]])
    with TestCase.assertRaises(Exception):
        _ = await VolatileMemoryStore.compute_similarity_scores(query_embedding, collection_embeddings)


def test_cosine_similarity_zero_collection():
    # Test case 3: Zero vector as collection_embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[0, 0, 0], [0, 0, 0]])
    with TestCase.assertRaises(Exception):
        _ = await VolatileMemoryStore.compute_similarity_scores(query_embedding, collection_embeddings)


def test_cosine_similarity_partial_zero_collection():
    # Test case 4: Partial zero vector as collection_embeddings
    query_embedding = np.array([1, 0, 1])
    collection_embeddings = np.array([[1, 0, 1], [0, 0, 0]])
    expected_scores = np.array([1.0, -1.0])
    scores = await VolatileMemoryStore.compute_similarity_scores(query_embedding, collection_embeddings)
    assert scores == expected_scores
