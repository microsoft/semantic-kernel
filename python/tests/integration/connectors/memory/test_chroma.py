# Copyright (c) Microsoft. All rights reserved.

import os
import shutil
import numpy as np
import pytest

from semantic_kernel.connectors.memory.chroma import ChromaMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import chromadb  # noqa: F401

    chromadb_installed = True
except ImportError:
    chromadb_installed = False

pytestmark = pytest.mark.skipif(
    not chromadb_installed, reason="chromadb is not installed"
)

@pytest.fixture
def setup_chroma():
    persist_directory = "local_chroma"
    memory = ChromaMemoryStore(persist_directory=persist_directory)
    yield memory
    os.remove(os.path.join(persist_directory, "chroma.sqlite3"))
    shutil.rmtree(persist_directory)


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        external_source_name="external source",
        additional_metadata="additional metadata",
        timestamp="timestamp",
    )


@pytest.fixture
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75]),
        description="description",
        external_source_name="external source",
        additional_metadata="additional metadata",
        timestamp="timestamp",
    )


def test_constructor(setup_chroma):
    memory = setup_chroma
    assert memory._client is not None


@pytest.mark.asyncio
async def test_create_and_get_collection_async(setup_chroma):
    memory = setup_chroma

    await memory.create_collection_async("test_collection")
    result = await memory.get_collection_async("test_collection")
    assert result.name == "test_collection"


@pytest.mark.asyncio
async def test_get_collections_async(setup_chroma):
    memory = setup_chroma

    await memory.create_collection_async("test_collection1")
    await memory.create_collection_async("test_collection2")
    await memory.create_collection_async("test_collection3")
    result = await memory.get_collections_async()

    assert len(result) == 3


@pytest.mark.asyncio
async def test_delete_collection_async(setup_chroma):
    memory = setup_chroma

    await memory.create_collection_async("test_collection")
    await memory.delete_collection_async("test_collection")
    result = await memory.get_collections_async()
    assert len(result) == 0

    await memory.create_collection_async("test_collection")
    await memory.delete_collection_async("TEST_COLLECTION")
    result = await memory.get_collections_async()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_does_collection_exist_async(setup_chroma):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    result = await memory.does_collection_exist_async("test_collection")
    assert result is True

    result = await memory.does_collection_exist_async("TEST_COLLECTION")
    assert result is True


@pytest.mark.asyncio
async def test_upsert_and_get_async(setup_chroma, memory_record1):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_async(collection.name, memory_record1)

    result = await memory.get_async(collection.name, "test_id1", True)
    assert result._id == "test_id1"
    assert result._text == "sample text1"
    assert result._is_reference is False
    assert np.array_equal(result.embedding, np.array([0.5, 0.5]))
    assert result._description == "description"
    assert result._external_source_name == "external source"
    assert result._additional_metadata == "additional metadata"
    assert result._timestamp == "timestamp"


@pytest.mark.asyncio
async def test_upsert_and_get_async_with_no_embedding(setup_chroma, memory_record1):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_async(collection.name, memory_record1)

    result = await memory.get_async(collection.name, "test_id1", False)
    assert result._id == "test_id1"
    assert result._text == "sample text1"
    assert result._is_reference is False
    assert result.embedding is None
    assert result._description == "description"
    assert result._external_source_name == "external source"
    assert result._additional_metadata == "additional metadata"
    assert result._timestamp == "timestamp"


@pytest.mark.asyncio
async def test_upsert_and_get_batch_async(setup_chroma, memory_record1, memory_record2):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_batch_async(collection.name, [memory_record1, memory_record2])

    result = await memory.get_batch_async(
        "test_collection", ["test_id1", "test_id2"], True
    )
    assert len(result) == 2
    assert result[0]._id == "test_id1"
    assert result[0]._text == "sample text1"
    assert result[0]._is_reference is False
    assert np.array_equal(result[0].embedding, np.array([0.5, 0.5]))
    assert result[0]._description == "description"
    assert result[0]._external_source_name == "external source"
    assert result[0]._additional_metadata == "additional metadata"
    assert result[0]._timestamp == "timestamp"


@pytest.mark.asyncio
async def test_remove_async(setup_chroma, memory_record1):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_async(collection.name, memory_record1)
    await memory.remove_async(collection.name, "test_id1")

    # memory.get_async should raise Exception if record is not found
    with pytest.raises(Exception):
        await memory.get_async(collection.name, "test_id1", True)


@pytest.mark.asyncio
async def test_remove_batch_async(setup_chroma, memory_record1, memory_record2):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_batch_async(collection.name, [memory_record1, memory_record2])
    await memory.remove_batch_async(collection.name, ["test_id1", "test_id2"])

    result = await memory.get_batch_async(
        "test_collection", ["test_id1", "test_id2"], True
    )
    assert result == []


@pytest.mark.asyncio
async def test_get_nearest_matches_async(setup_chroma, memory_record1, memory_record2):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_batch_async(collection.name, [memory_record1, memory_record2])

    results = await memory.get_nearest_matches_async(
        "test_collection", np.array([0.5, 0.5]), limit=2
    )

    assert len(results) == 2
    assert isinstance(results[0][0], MemoryRecord)
    assert results[0][1] == pytest.approx(1, abs=1e-5)


@pytest.mark.asyncio
async def test_get_nearest_match_async(setup_chroma, memory_record1, memory_record2):
    memory = setup_chroma
    await memory.create_collection_async("test_collection")
    collection = await memory.get_collection_async("test_collection")

    await memory.upsert_batch_async(collection.name, [memory_record1, memory_record2])

    result = await memory.get_nearest_match_async(
        "test_collection", np.array([0.5, 0.5])
    )

    assert len(result) == 2
    assert isinstance(result[0], MemoryRecord)
    assert result[1] == pytest.approx(1, abs=1e-5)
