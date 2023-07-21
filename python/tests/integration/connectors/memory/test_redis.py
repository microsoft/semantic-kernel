# Copyright (c) Microsoft. All rights reserved.

import os
from datetime import datetime

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.memory.redis import RedisMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import redis  # noqa: F401

    redis_installed = True
except ImportError:
    redis_installed = False

pytestmark = pytest.mark.skipif(not redis_installed, reason="Redis is not installed")


@pytest.fixture(scope="session")
def connection_string():
    if "Python_Integration_Tests" in os.environ:
        connection_string = os.environ["Redis__Configuration"]
    else:
        # Load credentials from .env file, or go to default if not found
        try:
            connection_string = sk.redis_settings_from_dot_env()
        except Exception:
            connection_string = "redis://localhost:6379"

    return connection_string


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


def test_constructor_and_ping(connection_string):
    memory = RedisMemoryStore(connection_string)
    assert memory.ping()


def test_configure(connection_string):
    memory = RedisMemoryStore(connection_string)

    # Test current port
    port_setup = memory._database.config_get("port")
    memory.configure(port_setup)
    assert memory.ping()

    # Test faulty port
    port_setup["port"] = "not_number"
    try:
        memory.configure(port_setup)
    except redis.exceptions.ResponseError:
        pass
    assert memory.ping()


@pytest.mark.asyncio
async def test_create_and_does_collection_exist_async(connection_string):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection")
    exists = await memory.does_collection_exist_async("test_collection")
    assert exists


@pytest.mark.asyncio
async def test_delete_collection_async(connection_string):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection")
    await memory.delete_collection_async("test_collection")

    exists = await memory.does_collection_exist_async("test_collection")
    assert not exists

    # Delete a non-existent collection with no error
    await memory.delete_collection_async("test_collection")


@pytest.mark.asyncio
async def test_get_collections_async(connection_string):
    memory = RedisMemoryStore(connection_string)

    collection_names = ["c1", "c2", "c3"]
    for c_n in collection_names:
        await memory.create_collection_async(c_n)

    names_from_func = await memory.get_collections_async()
    for c_n in collection_names:
        assert c_n in names_from_func
        await memory.delete_collection_async(c_n)


@pytest.mark.asyncio
async def test_does_collection_exist_async(connection_string):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection")
    exists = await memory.does_collection_exist_async("test_collection")
    assert exists

    await memory.delete_collection_async("test_collection")
    exists = await memory.does_collection_exist_async("test_collection")
    assert not exists


@pytest.mark.asyncio
async def test_upsert_async_and_get_async(connection_string, memory_record1):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection", vector_dimension=2)

    # Insert a record
    await memory.upsert_async("test_collection", memory_record1)
    fetch_1 = await memory.get_async("test_collection", memory_record1._id, True)
    assert fetch_1 is not None, "Could not get record"
    assert fetch_1._id == memory_record1._id
    assert fetch_1._timestamp == memory_record1._timestamp
    assert fetch_1._is_reference == memory_record1._is_reference
    assert fetch_1._external_source_name == memory_record1._external_source_name
    assert fetch_1._description == memory_record1._description
    assert fetch_1._text == memory_record1._text
    assert fetch_1._additional_metadata == memory_record1._additional_metadata
    for expected, actual in zip(fetch_1.embedding, memory_record1.embedding):
        assert expected == actual, "Did not retain correct embedding"

    # Update a record
    original_text = memory_record1._text
    memory_record1._text = "updated sample text1"
    await memory.upsert_async("test_collection", memory_record1)
    fetch_1 = await memory.get_async("test_collection", memory_record1._id, True)
    assert fetch_1 is not None, "Could not get record"
    assert fetch_1._text == memory_record1._text
    memory_record1._text = original_text


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(
    connection_string, memory_record1, memory_record2
):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection", vector_dimension=2)

    ids = [memory_record1._id, memory_record2._id]
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])

    fetched = await memory.get_batch_async("test_collection", ids, True)
    assert len(fetched) > 0, "Could not get records"
    for f in fetched:
        assert f._id in ids


@pytest.mark.asyncio
async def test_remove_async(connection_string, memory_record1):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection", vector_dimension=2)

    await memory.upsert_async("test_collection", memory_record1)
    await memory.remove_async("test_collection", memory_record1._id)
    get_record = await memory.get_async("test_collection", memory_record1._id, False)
    assert not get_record, "Record was not removed"


@pytest.mark.asyncio
async def test_remove_batch_async(connection_string, memory_record1, memory_record2):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection", vector_dimension=2)

    ids = [memory_record1._id, memory_record2._id]
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])
    await memory.remove_batch_async("test_collection", ids)
    get_records = await memory.get_batch_async("test_collection", ids, False)
    assert len(get_records) == 0, "Records were not removed"


@pytest.mark.asyncio
async def test_get_nearest_match_async(
    connection_string, memory_record1, memory_record2
):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection", vector_dimension=2)
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
    )
    assert result is not None
    assert result[0]._id == memory_record1._id
    assert result[0]._text == memory_record1._text
    assert result[0]._description == memory_record1._description
    assert result[0]._additional_metadata == memory_record1._additional_metadata
    assert result[0]._timestamp == memory_record1._timestamp
    for i in range(len(result[0]._embedding)):
        assert result[0]._embedding[i] == memory_record1._embedding[i]


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    connection_string, memory_record1, memory_record2, memory_record3
):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection", vector_dimension=2)
    await memory.upsert_batch_async(
        "test_collection", [memory_record1, memory_record2, memory_record3]
    )
    test_embedding = memory_record2.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.025

    result = await memory.get_nearest_matches_async(
        "test_collection",
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )

    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
