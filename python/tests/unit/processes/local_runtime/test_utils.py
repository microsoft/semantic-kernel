# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from semantic_kernel.connectors.memory.chroma.utils import (
    camel_to_snake,
    chroma_compute_similarity_scores,
    query_results_to_records,
)
from semantic_kernel.memory.memory_record import MemoryRecord


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("CamelCaseString", "camel_case_string"),
        ("simpleExample", "simple_example"),
        ("", ""),  # Empty string edge case
        ("ALLCAPS", "a_l_l_c_a_p_s"),  # All uppercase
        ("already_snake", "already_snake"),  # Already in snake case
        ("someXMLString", "some_x_m_l_string"),  # Mixed uppercase letters
    ],
)
def test_camel_to_snake(input_str: str, expected: str) -> None:
    """Test the camel_to_snake function with various input strings."""
    # Arrange & Act
    result = camel_to_snake(input_str)

    # Assert
    assert result == expected, f"Input '{input_str}' should convert to '{expected}'"


def test_query_results_to_records_single_result_with_embedding() -> None:
    """Test query_results_to_records function with a single result including embeddings."""
    # Arrange
    sample_id = "test_id"
    sample_document = "sample text"
    sample_embedding = [0.1, 0.2, 0.3]
    sample_metadata = {
        "is_reference": "True",
        "external_source_name": "test_source",
        "id": "metadata_id",
        "description": "metadata description",
        "additional_metadata": "meta",
        "timestamp": "2023-01-01",
    }

    results = {
        "ids": [sample_id],
        "documents": [sample_document],
        "embeddings": [sample_embedding],
        "metadatas": [sample_metadata],
    }

    # Act
    records = query_results_to_records(results, with_embedding=True)  # type: ignore

    # Assert
    assert len(records) == 1, "Expected exactly one MemoryRecord returned"
    record = records[0]
    assert isinstance(record, MemoryRecord)
    assert record.embedding is not None, "Embedding should not be None when with_embedding=True"
    assert np.allclose(record.embedding, sample_embedding), "Embeddings do not match"
    assert record.id == sample_metadata["id"], "ID mismatch"
    assert record.text == sample_document, "Text mismatch"
    assert record.description == sample_metadata["description"], "Description mismatch"
    # Changed to private attribute to fix lint error
    assert record._is_reference is True, "is_reference mismatch"
    assert record.timestamp == sample_metadata["timestamp"], "Timestamp mismatch"


def test_query_results_to_records_single_result_without_embedding() -> None:
    """Test query_results_to_records function with a single result but no embeddings."""
    # Arrange
    sample_id = "test_id"
    sample_document = "sample text"
    sample_metadata = {
        "is_reference": "False",
        "external_source_name": "test_source",
        "id": "metadata_id",
        "description": "metadata description",
        "additional_metadata": "meta",
        "timestamp": "2023-01-01",
    }

    results = {
        "ids": [sample_id],
        "documents": [sample_document],
        # embeddings is not present in the results, simulating no embeddings scenario
        "metadatas": [sample_metadata],
    }

    # Act
    records = query_results_to_records(results, with_embedding=False)  # type: ignore

    # Assert
    assert len(records) == 1, "Expected exactly one MemoryRecord returned"
    record = records[0]
    assert isinstance(record, MemoryRecord)
    assert record.embedding is None, "Embedding should be None when with_embedding=False"
    assert record.id == sample_metadata["id"], "ID mismatch"
    assert record.text == sample_document, "Text mismatch"
    assert record.description == sample_metadata["description"], "Description mismatch"
    # Changed to private attribute to fix lint error
    assert record._is_reference is False, "is_reference mismatch"
    assert record.timestamp == sample_metadata["timestamp"], "Timestamp mismatch"


def test_query_results_to_records_multiple_results_with_embedding() -> None:
    """Test query_results_to_records function with multiple results and embeddings."""
    # Arrange
    results = {
        "ids": [["id1", "id2"]],
        "documents": [["doc1", "doc2"]],
        "embeddings": [[[0.1, 0.2], [0.3, 0.4]]],
        "metadatas": [
            [
                {
                    "is_reference": "True",
                    "external_source_name": "source1",
                    "id": "id1",
                    "description": "desc1",
                    "additional_metadata": "meta1",
                    "timestamp": "2023-01-01",
                },
                {
                    "is_reference": "False",
                    "external_source_name": "source2",
                    "id": "id2",
                    "description": "desc2",
                    "additional_metadata": "meta2",
                    "timestamp": "2023-01-02",
                },
            ]
        ],
    }

    # Act
    records = query_results_to_records(results, with_embedding=True)  # type: ignore

    # Assert
    assert len(records) == 2, "Expected two MemoryRecord objects returned"
    for i, record in enumerate(records):
        assert isinstance(record, MemoryRecord)
        assert record.id == results["metadatas"][0][i]["id"], "ID mismatch"
        assert np.allclose(record.embedding, results["embeddings"][0][i]), "Embedding mismatch"
        assert record.text == results["documents"][0][i], "Text mismatch"
        assert record.description == results["metadatas"][0][i]["description"], "Description mismatch"


def test_query_results_to_records_no_results() -> None:
    """Test query_results_to_records with results that contain empty 'ids' leading to an IndexError being handled."""
    # Arrange
    results = {
        "ids": [],
        "documents": [],
        "embeddings": [],
        "metadatas": [],
    }

    # Act
    records = query_results_to_records(results, with_embedding=True)  # type: ignore

    # Assert
    # Should return an empty list
    assert records == [], "Expected an empty list when 'ids' is empty"


@patch("semantic_kernel.connectors.memory.chroma.utils.logger")
def test_chroma_compute_similarity_scores(mock_logger: MagicMock) -> None:
    """Test normal usage of chroma_compute_similarity_scores with valid embeddings."""
    # Arrange
    query_embedding = np.array([1, 2, 3], dtype=float)
    collection = np.array(
        [
            [1, 2, 3],
            [2, 3, 4],
        ],
        dtype=float,
    )

    # Act
    scores = chroma_compute_similarity_scores(query_embedding, collection)

    # Assert
    assert len(scores) == 2, "Should compute scores for the entire collection"
    for score in scores:
        assert score != -1, "All vectors are non-zero, so no -1 entries expected"
    mock_logger.warning.assert_not_called()


@patch("semantic_kernel.connectors.memory.chroma.utils.logger")
def test_chroma_compute_similarity_scores_some_zero_vectors(mock_logger: MagicMock) -> None:
    """Test chroma_compute_similarity_scores when some vectors are zero vectors in the collection."""
    # Arrange
    query_embedding = np.array([1, 2, 3], dtype=float)
    collection = np.array(
        [
            [0, 0, 0],  # Zero vector
            [1, 1, 1],
            [0, 0, 0],  # Another zero vector
        ],
        dtype=float,
    )

    # Act
    scores = chroma_compute_similarity_scores(query_embedding, collection)

    # Assert
    assert len(scores) == 3
    assert scores[0] == -1.0, "Expected -1 for zero vector"
    assert scores[2] == -1.0, "Expected -1 for zero vector"
    assert scores[1] != -1.0, "Non-zero vector should have a valid score"
    mock_logger.warning.assert_called_once()


def test_chroma_compute_similarity_scores_all_zero_vectors_raises_error() -> None:
    """Test chroma_compute_similarity_scores when query embedding and/or collection embeddings are all zero, resulting in ValueError."""  # noqa: E501
    # Arrange
    query_embedding = np.array([0, 0, 0], dtype=float)
    collection = np.array(
        [
            [0, 0, 0],
            [0, 0, 0],
        ],
        dtype=float,
    )

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        _ = chroma_compute_similarity_scores(query_embedding, collection)
    assert "Invalid vectors" in str(exc_info.value), "Expected ValueError with 'Invalid vectors' message"
