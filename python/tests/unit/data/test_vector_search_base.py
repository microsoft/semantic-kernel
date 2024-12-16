# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions


async def test_search(vector_store_record_collection: VectorSearchBase):
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    results = await vector_store_record_collection._inner_search(
        options=VectorSearchOptions(), search_text="test_content"
    )
    records = [rec async for rec in results.results]
    assert records[0].record == record
