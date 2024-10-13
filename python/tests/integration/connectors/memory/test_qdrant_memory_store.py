# Copyright (c) Microsoft. All rights reserved.

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head

import pytest

from semantic_kernel.connectors.memory.qdrant import QdrantMemoryStore
from datetime import datetime
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

import pytest

from semantic_kernel.connectors.memory.qdrant import QdrantMemoryStore

try:
    import qdrant_client  # noqa: F401

    qdrant_client_installed = True
    TEST_VECTOR_SIZE = 2
except ImportError:
    qdrant_client_installed = False

pytestmark = pytest.mark.skipif(
    not qdrant_client_installed, reason="qdrant-client is not installed"
)


<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
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

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
def test_qdrant_constructor():
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)
    assert qdrant_mem_store._qdrantclient is not None


@pytest.mark.asyncio
async def test_create_and_get_collection():
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    result = await qdrant_mem_store.get_collection("test_collection")
async def test_create_and_get_collection_async():
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    result = await qdrant_mem_store.get_collection("test_collection")
    assert result.status == "green"


@pytest.mark.asyncio
async def test_get_collections():
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection1")
    await qdrant_mem_store.create_collection("test_collection2")
    await qdrant_mem_store.create_collection("test_collection3")
    result = await qdrant_mem_store.get_collections()
async def test_get_collections_async():
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection1")
    await qdrant_mem_store.create_collection("test_collection2")
    await qdrant_mem_store.create_collection("test_collection3")
    result = await qdrant_mem_store.get_collections()
    assert len(result) == 3


@pytest.mark.asyncio
async def test_delete_collection():
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection(
        "test_collection4",
    )
    result = await qdrant_mem_store.get_collections()
    assert len(result) == 1
    await qdrant_mem_store.delete_collection("test_collection4")
    result = await qdrant_mem_store.get_collections()
async def test_delete_collection_async():
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection(
        "test_collection4",
    )
    result = await qdrant_mem_store.get_collections()
    assert len(result) == 1
    await qdrant_mem_store.delete_collection("test_collection4")
    result = await qdrant_mem_store.get_collections()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_does_collection_exist():
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    result = await qdrant_mem_store.does_collection_exist("test_collection")
    assert result is True
    result = await qdrant_mem_store.does_collection_exist("test_collection2")
async def test_does_collection_exist_async():
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    result = await qdrant_mem_store.does_collection_exist("test_collection")
    assert result is True
    result = await qdrant_mem_store.does_collection_exist("test_collection2")
    assert result is False


@pytest.mark.asyncio
async def test_upsert_and_get(memory_record1):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert("test_collection", memory_record1)
    result = await qdrant_mem_store.get("test_collection", memory_record1._id)
    assert result is not None
    assert result._id == memory_record1._id
    assert result._text == memory_record1._text
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert("test_collection", memory_record1)
    result = await qdrant_mem_store.get("test_collection", memory_record1._id)
    assert result is not None
    assert result._id == memory_record1._id
    assert result._text == memory_record1._text


@pytest.mark.asyncio
async def test_overwrite(memory_record1):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert("test_collection", memory_record1)
    await qdrant_mem_store.upsert("test_collection", memory_record1)


@pytest.mark.asyncio
async def test_upsert_batch_and_get_batch(memory_record1, memory_record2):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
        "test_collection", [memory_record1, memory_record2]
    )

    results = await qdrant_mem_store.get_batch(
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
async def test_upsert_async_and_get_async(memory_record1):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection_async("test_collection")
    await qdrant_mem_store.upsert_async("test_collection", memory_record1)
    result = await qdrant_mem_store.get_async(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None
    assert result._id == memory_record1._id
    assert result._text == memory_record1._text
    assert result._timestamp == memory_record1._timestamp
    for i in range(len(result._embedding)):
        assert result._embedding[i] == memory_record1._embedding[i]
<<<<<<< div
<<<<<<< div
>>>>>>> origin/main
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head


@pytest.mark.asyncio
async def test_overwrite(memory_record1):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert("test_collection", memory_record1)
    await qdrant_mem_store.upsert("test_collection", memory_record1)


@pytest.mark.asyncio
async def test_upsert_batch_and_get_batch(memory_record1, memory_record2):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
        "test_collection", [memory_record1, memory_record2]
    )

    results = await qdrant_mem_store.get_batch(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        "test_collection",
        [memory_record1._id, memory_record2._id],
        with_embeddings=True,
    )

    assert len(results) == 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


@pytest.mark.asyncio
async def test_remove(memory_record1):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert("test_collection", memory_record1)

    result = await qdrant_mem_store.get(
async def test_remove_async(memory_record1):
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert("test_collection", memory_record1)

    result = await qdrant_mem_store.get(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None

    await qdrant_mem_store.remove("test_collection", memory_record1._id)
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head

    result = await qdrant_mem_store.get(
    await qdrant_mem_store.remove_async("test_collection", memory_record1._id)
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    result = await qdrant_mem_store.get(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is None


@pytest.mark.asyncio
async def test_remove_batch(memory_record1, memory_record2):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
        "test_collection", [memory_record1, memory_record2]
    )
    result = await qdrant_mem_store.get(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None
    result = await qdrant_mem_store.get(
        "test_collection", memory_record2._id, with_embedding=True
    )
    assert result is not None
    await qdrant_mem_store.remove_batch(
        "test_collection", [memory_record1._id, memory_record2._id]
    )
    result = await qdrant_mem_store.get(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is None
    result = await qdrant_mem_store.get(
async def test_remove_batch_async(memory_record1, memory_record2):
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
        "test_collection", [memory_record1, memory_record2]
    )
    result = await qdrant_mem_store.get(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None
    result = await qdrant_mem_store.get(
        "test_collection", memory_record2._id, with_embedding=True
    )
    assert result is not None
    await qdrant_mem_store.remove_batch(
        "test_collection", [memory_record1._id, memory_record2._id]
    )
    result = await qdrant_mem_store.get(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is None
    result = await qdrant_mem_store.get(
        "test_collection", memory_record2._id, with_embedding=True
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_nearest_match(memory_record1, memory_record2):
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
async def test_get_nearest_match_async(memory_record1, memory_record2):
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
        "test_collection", [memory_record1, memory_record2]
    )
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await qdrant_mem_store.get_nearest_match(
        "test_collection", test_embedding, min_relevance_score=0.0
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> origin/main
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> Stashed changes
<<<<<<< div
=======
    result = await qdrant_mem_store.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
>>>>>>> main
=======
>>>>>>> head
    )
    assert result is not None
    assert result[0]._id == memory_record1._id
    assert result[0]._text == memory_record1._text
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head


@pytest.mark.asyncio
async def test_get_nearest_matches(memory_record1, memory_record2, memory_record3):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
    assert result[0]._timestamp == memory_record1._timestamp
    for i in range(len(result[0]._embedding)):
        assert result[0]._embedding[i] == memory_record1._embedding[i]
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head


@pytest.mark.asyncio
async def test_get_nearest_matches(memory_record1, memory_record2, memory_record3):
    qdrant_mem_store = QdrantMemoryStore(vector_size=TEST_VECTOR_SIZE, local=True)

    await qdrant_mem_store.create_collection("test_collection")
    await qdrant_mem_store.upsert_batch(
        "test_collection", [memory_record1, memory_record2, memory_record3]
    )
    test_embedding = memory_record2.embedding
    test_embedding[0] = test_embedding[0] + 0.025

    result = await qdrant_mem_store.get_nearest_matches(
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
    result = await qdrant_mem_store.get_nearest_matches_async(
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
    result = await qdrant_mem_store.get_nearest_matches_async(
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        "test_collection",
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )
    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
