# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, cast

import numpy as np
import pytest
from chromadb.api.types import QueryResult

from semantic_kernel.connectors.memory.chroma.utils import (
    chroma_compute_similarity_scores,
    query_results_to_records,
)

# def test_camel_to_snake_basic_cases() -> None:
#     """
#     Test converting various camelCase strings to snake_case.

#     This covers standard conversions, acronyms, numbers, and edge cases.
#     """
#     # Standard conversions
#     assert camel_to_snake("camelCaseTest") == "camel_case_test"
#     assert camel_to_snake("CamelCase") == "camel_case"
#     # Already snake or lowercase remains unchanged
#     assert camel_to_snake("already_snake") == "already_snake"
#     assert camel_to_snake("lowercase") == "lowercase"
#     # Acronyms and consecutive uppercase letters
#     assert camel_to_snake("XMLHttpRequest") == "xml_http_request"
#     assert camel_to_snake("HTTPServerError") == "http_server_error"
#     # Numbers in string
#     assert camel_to_snake("Test123Case") == "test123_case"
#     # Empty string edge case
#     assert camel_to_snake("") == ""


def test_query_results_to_records_shallow_and_embedding_flags() -> None:
    """
    Test query_results_to_records with a single (flat) record and both embedding flags.

    Validate transformation of shallow dict input and check both with_embedding True/False.
    """
    # Prepare flat-style results (shallow lists)
    meta: Any = {
        "is_reference": "True",
        "external_source_name": "sourceA",
        "id": "meta123",
        "description": "a record",
        "additional_metadata": "extra",
        "timestamp": "2022-05-01T12:00:00",
    }
    results_flat: Any = {
        "ids": ["key1"],
        "documents": ["document text"],
        "embeddings": [[0.1, 0.2, 0.3]],
        "metadatas": [meta],
    }

    # With embedding included
    records_with_emb = query_results_to_records(cast(QueryResult, results_flat.copy()), with_embedding=True)
    assert len(records_with_emb) == 1
    rec1 = records_with_emb[0]
    # Public properties
    assert rec1.id == "meta123"
    assert rec1.text == "document text"
    np.testing.assert_array_equal(rec1.embedding, np.array([0.1, 0.2, 0.3]))
    assert rec1.additional_metadata == "extra"
    assert rec1.description == "a record"
    assert rec1.timestamp == "2022-05-01T12:00:00"
    # Private/internal attributes
    assert rec1._is_reference is True
    assert rec1._external_source_name == "sourceA"
    assert rec1._key == "key1"

    # Without embedding (embedding should be None)
    records_no_emb = query_results_to_records(cast(QueryResult, results_flat.copy()), with_embedding=False)
    assert len(records_no_emb) == 1
    rec2 = records_no_emb[0]
    assert rec2.embedding is None
    assert rec2._key == "key1"


def test_query_results_to_records_nested_multiple() -> None:
    """
    Test query_results_to_records with nested lists and multiple records.

    Ensure nested lists are handled correctly and multiple records extracted.
    """
    # Prepare nested-style results
    meta1: Any = {
        "is_reference": "False",
        "external_source_name": "src1",
        "id": "m1",
        "description": "desc1",
        "additional_metadata": "md1",
        "timestamp": "t1",
    }
    meta2: Any = {
        "is_reference": "True",
        "external_source_name": "src2",
        "id": "m2",
        "description": "desc2",
        "additional_metadata": "md2",
        "timestamp": "t2",
    }
    results_nested: Any = {
        "ids": [["k1", "k2"]],
        "documents": [["doc1", "doc2"]],
        "embeddings": [[[1, 0], [0, 1]]],
        "metadatas": [[meta1, meta2]],
    }
    records = query_results_to_records(cast(QueryResult, results_nested.copy()), with_embedding=True)
    # Should produce two records
    assert len(records) == 2

    # First record checks
    r0 = records[0]
    assert r0._key == "k1"
    assert r0.id == "m1"
    assert r0._is_reference is False
    np.testing.assert_array_equal(r0.embedding, np.array([1, 0]))

    # Second record checks
    r1 = records[1]
    assert r1._key == "k2"
    assert r1.id == "m2"
    assert r1._is_reference is True
    np.testing.assert_array_equal(r1.embedding, np.array([0, 1]))


def test_query_results_to_records_empty_ids_returns_empty_list() -> None:
    """
    If results contain no ids, function should return an empty list without raising.
    """
    empties: Any = {"ids": [], "documents": [], "embeddings": [], "metadatas": []}
    result = query_results_to_records(cast(QueryResult, empties), with_embedding=True)
    assert result == []


def test_chroma_compute_similarity_scores_all_valid_no_warnings(caplog) -> None:
    """
    Test similarity scores when all vectors are non-zero; no warnings should be emitted.
    """
    caplog.set_level(logging.WARNING)
    emb_q = np.array([1.0, 0.0])
    emb_arr = np.array([[1.0, 0.0], [0.0, 1.0]])
    scores = chroma_compute_similarity_scores(emb_q, emb_arr)
    # Expect cosine similarities [1, 0]
    assert pytest.approx(scores.tolist()) == [1.0, 0.0]
    # No warnings should be logged
    assert "Some vectors in the embedding collection" not in caplog.text


def test_chroma_compute_similarity_scores_with_zero_vectors_warns(caplog) -> None:
    """
    Test similarity scores when some embedding vectors are zero; should generate warning and leave -1 for zero vectors.
    """
    caplog.set_level(logging.WARNING)
    emb_q = np.array([1.0, 0.0])
    emb_arr = np.array([[1.0, 0.0], [0.0, 0.0]])
    scores = chroma_compute_similarity_scores(emb_q, emb_arr)
    # First index valid: 1.0, second invalid: -1.0
    assert pytest.approx(scores.tolist()) == [1.0, -1.0]
    # Warning logged for zero vectors
    assert "Some vectors in the embedding collection are zero vectors" in caplog.text


def test_chroma_compute_similarity_scores_all_invalid_raises() -> None:
    """
    Test that if all vectors are invalid (zero), a ValueError is raised.
    """
    emb_q = np.array([0.0, 0.0])
    emb_arr = np.array([[1.0, 0.0], [0.0, 1.0]])  # non-zero collection
    with pytest.raises(ValueError) as excinfo1:
        chroma_compute_similarity_scores(emb_q, emb_arr)
    assert "Invalid vectors" in str(excinfo1.value)

    emb_q2 = np.array([1.0, 0.0])
    emb_arr2 = np.array([[0.0, 0.0], [0.0, 0.0]])  # all zero collection
    with pytest.raises(ValueError) as excinfo2:
        chroma_compute_similarity_scores(emb_q2, emb_arr2)
    assert "Invalid vectors" in str(excinfo2.value)
