# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime

import numpy as np
import pytest

try:
    from semantic_kernel.connectors.memory.azure_cosmosdb.azure_cosmos_db_memory_store import (
        AzureCosmosDBMemoryStore,
    )

    azure_cosmosdb_memory_store_installed = True
except AssertionError:
    azure_cosmosdb_memory_store_installed = False

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

index_name = "sk_test_vector_search_index"
vector_dimensions = 1536
num_lists = 1
similarity = "COS"
collection_name = "sk_test_collection"
database_name = "sk_test_database"

pytestmark = pytest.mark.skipif(
    not azure_cosmosdb_memory_store_installed,
    reason="Azure CosmosDB Memory Store is not installed",
)


def create_embedding(non_zero_pos: int) -> np.ndarray:
    # Create a NumPy array with a single non-zero value of dimension 1546
    embedding = np.zeros(vector_dimensions)
    embedding[non_zero_pos - 1] = 1.0
    return embedding


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=create_embedding(non_zero_pos=1),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=create_embedding(non_zero_pos=2),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
def memory_record3():
    return MemoryRecord(
        id="test_id3",
        text="sample text3",
        is_reference=False,
        embedding=create_embedding(non_zero_pos=3),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


async def azurecosmosdb_memorystore() -> MemoryStoreBase:
    store = await AzureCosmosDBMemoryStore.create(
        database_name=database_name,
        collection_name=collection_name,
        index_name=index_name,
        vector_dimensions=vector_dimensions,
        num_lists=num_lists,
        similarity=similarity,
    )
    return store


@pytest.mark.asyncio
async def test_create_get_drop_exists_collection():
    store = await azurecosmosdb_memorystore()
    test_collection = "test_collection"

    await store.create_collection(test_collection)

    collection_list = await store.get_collections()
    assert test_collection in collection_list

    await store.delete_collection(test_collection)

    result = await store.does_collection_exist(test_collection)
    assert result is True


@pytest.mark.asyncio
async def test_upsert_and_get_and_remove(
    memory_record1: MemoryRecord,
):
    store = await azurecosmosdb_memorystore()
    doc_id = await store.upsert(str(), memory_record1)
    assert doc_id == memory_record1._id

    result = await store.get(str(), memory_record1._id, with_embedding=True)

    assert result is not None
    assert result._id == memory_record1._id
    assert all(result._embedding[i] == memory_record1._embedding[i] for i in range(len(result._embedding)))

    await store.remove(str(), memory_record1._id)


@pytest.mark.asyncio
async def test_upsert_batch_and_get_batch_remove_batch(memory_record2: MemoryRecord, memory_record3: MemoryRecord):
    store = await azurecosmosdb_memorystore()
    doc_ids = await store.upsert_batch(str(), [memory_record2, memory_record3])
    assert len(doc_ids) == 2
    assert all(doc_id in [memory_record2._id, memory_record3._id] for doc_id in doc_ids)

    results = await store.get_batch(str(), [memory_record2._id, memory_record3._id], with_embeddings=True)

    assert len(results) == 2
    assert all(result._id in [memory_record2._id, memory_record3._id] for result in results)

    await store.remove_batch(str(), [memory_record2._id, memory_record3._id])


@pytest.mark.asyncio
async def test_get_nearest_match(memory_record1: MemoryRecord, memory_record2: MemoryRecord):
    store = await azurecosmosdb_memorystore()
    await store.upsert_batch(str(), [memory_record1, memory_record2])
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.1

    result = await store.get_nearest_match(
        collection_name, test_embedding, min_relevance_score=0.0, with_embedding=True
    )

    assert result is not None
    assert result[0]._id == memory_record1._id
    assert all(result[0]._embedding[i] == memory_record1._embedding[i] for i in range(len(result[0]._embedding)))

    await store.remove_batch(str(), [memory_record1._id, memory_record2._id])


@pytest.mark.asyncio
async def test_get_nearest_matches(
    memory_record1: MemoryRecord,
    memory_record2: MemoryRecord,
    memory_record3: MemoryRecord,
):
    store = await azurecosmosdb_memorystore()
    await store.upsert_batch(str(), [memory_record1, memory_record2, memory_record3])
    test_embedding = memory_record2.embedding.copy()
    test_embedding[0] = test_embedding[4] + 0.1

    result = await store.get_nearest_matches(
        str(), test_embedding, limit=2, min_relevance_score=0.0, with_embeddings=True
    )
    assert len(result) == 2
    assert all(result[i][0]._id in [memory_record1._id, memory_record2._id] for i in range(2))

    await store.remove_batch(str(), [memory_record1._id, memory_record2._id, memory_record3._id])
