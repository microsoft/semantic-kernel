# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime

import numpy as np
import pytest

from semantic_kernel.connectors.memory.qdrant import QdrantMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import qdrant_client  # noqa: F401

    qdrant_client_installed = True
    TEST_VECTOR_SIZE = 2
except ImportError:
    qdrant_client_installed = False

pytestmark = pytest.mark.skipif(
    not qdrant_client_installed, reason="qdrant-client is not installed"
)


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
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
        embedding=np.array([0.25, 0.75]),
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
        embedding=np.array([0.25, 0.80]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


def test_qdrant_constructor():
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)
    assert qdrant_mem_store._qdrantclient is not None


@pytest.mark.asyncio
async def test_create_and_get_collection_async():
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    result = await qdrant_mem_store.get_collection_async("test_collection")
    assert result.status == "green"


@pytest.mark.asyncio
async def test_get_collections_async():
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection1")
    await qdrant_mem_store.create_collection_async("test_collection2")
    await qdrant_mem_store.create_collection_async("test_collection3")
    result = await qdrant_mem_store.get_collections_async()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_delete_collection_async():
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async(
        "test_collection4",
    )
    result = await qdrant_mem_store.get_collections_async()
    assert len(result) == 1
    await qdrant_mem_store.delete_collection_async("test_collection4")
    result = await qdrant_mem_store.get_collections_async()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_does_collection_exist_async():
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    result = await qdrant_mem_store.does_collection_exist_async("test_collection")
    assert result is True
    result = await qdrant_mem_store.does_collection_exist_async("test_collection2")
    assert result is False


@pytest.mark.asyncio
async def test_upsert_async_and_get_async(memory_record1):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_async("test_collection", memory_record1)
    result = await qdrant_mem_store.get_async("test_collection", memory_record1._id)
    assert result is not None
    assert result._id == memory_record1._id
    assert result._text == memory_record1._text
    assert result._timestamp == memory_record1._timestamp


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(memory_record1, memory_record2):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_batch_async(
        "test_collection", [memory_record1, memory_record2]
    )

    results = await qdrant_mem_store.get_batch_async(
        "test_collection",
        [memory_record1._id, memory_record2._id],
        with_embeddings=True,
    )

    assert len(results) == 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


@pytest.mark.asyncio
async def test_remove_async(memory_record1):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_async("test_collection", memory_record1)

    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None

    await qdrant_mem_store.remove_async("test_collection", memory_record1._id)

    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is None


@pytest.mark.asyncio
async def test_remove_batch_async(memory_record1, memory_record2):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_batch_async(
        "test_collection", [memory_record1, memory_record2]
    )
    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None
    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record2._id, with_embedding=True
    )
    assert result is not None
    await qdrant_mem_store.remove_batch_async(
        "test_collection", [memory_record1._id, memory_record2._id]
    )
    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is None
    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record2._id, with_embedding=True
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_nearest_match_async(memory_record1, memory_record2):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_batch_async(
        "test_collection", [memory_record1, memory_record2]
    )
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0
    )
    assert result is not None
    assert result[0]._id == memory_record1._id
    assert result[0]._text == memory_record1._text
    assert result[0]._timestamp == memory_record1._timestamp


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    memory_record1, memory_record2, memory_record3
):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_batch_async(
        "test_collection", [memory_record1, memory_record2, memory_record3]
    )
    test_embedding = memory_record2.embedding
    test_embedding[0] = test_embedding[0] + 0.025

    result = await qdrant_mem_store.get_nearest_matches_async(
        "test_collection",
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )
    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
