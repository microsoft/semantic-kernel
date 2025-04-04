# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import MagicMock

import pytest

from semantic_kernel.data.vector_search import VectorSearchBase, VectorSearchOptions
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreModelDeserializationException


async def test_search(vector_store_record_collection: VectorSearchBase):
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    results = await vector_store_record_collection._inner_search(
        options=VectorSearchOptions(), search_text="test_content"
    )
    records = [rec async for rec in results.results]
    assert records[0].record == record


@pytest.mark.parametrize("include_vectors", [True, False])
async def test_get_vector_search_results(vector_store_record_collection: VectorSearchBase, include_vectors: bool):
    options = VectorSearchOptions(include_vectors=include_vectors)
    results = [{"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}]
    async for result in vector_store_record_collection._get_vector_search_results_from_results(
        results=results, options=options
    ):
        assert result.record == results[0] if include_vectors else {"id": "test_id", "content": "test_content"}
        break


async def test_get_vector_search_results_fail(vector_store_record_collection: VectorSearchBase):
    vector_store_record_collection.data_model_definition.vector_fields[0].deserialize_function = MagicMock(
        side_effect=Exception
    )
    options = VectorSearchOptions(include_vectors=True)
    results = [{"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}]
    with pytest.raises(VectorStoreModelDeserializationException):
        async for result in vector_store_record_collection._get_vector_search_results_from_results(
            results=results, options=options
        ):
            assert result.record == results[0]
            break
