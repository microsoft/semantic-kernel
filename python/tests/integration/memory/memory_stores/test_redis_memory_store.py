# Copyright (c) Microsoft. All rights reserved.

import asyncio
import platform

import pytest

from semantic_kernel.connectors.memory.redis import RedisMemoryStore
from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings

try:
    import redis  # noqa: F401

    redis_installed = True
    TEST_COLLECTION_NAME = "test_collection"
    TEST_VEC_SIZE = 2
except ImportError:
    redis_installed = False

pytestmark = pytest.mark.skipif(not redis_installed, reason="Redis is not installed")

pytestmark = pytest.mark.skipif(
    platform.system() != "Linux",
    reason="local redis docker container is not available on all non-Linux platforms",
)


@pytest.fixture(scope="session")
def connection_string():
    try:
        redis_settings = RedisSettings()
        if redis_settings.connection_string:
            return redis_settings.connection_string.get_secret_value()
        return "redis://localhost:6379"
    except Exception:
        pytest.skip("Redis connection string not found in env vars.")


@pytest.fixture
def memory_store(connection_string):
    # Setup and yield
    redis_mem_store = RedisMemoryStore(connection_string, vector_size=TEST_VEC_SIZE)
    yield redis_mem_store

    # Delete test collection after test
    asyncio.run(redis_mem_store.delete_collection(TEST_COLLECTION_NAME))


def test_constructor(memory_store):
    memory = memory_store
    assert memory and memory._database.ping()


async def test_create_and_does_collection_exist(memory_store):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)
    exists = await memory.does_collection_exist(TEST_COLLECTION_NAME)
    assert exists


async def test_delete_collection(memory_store):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)
    await memory.delete_collection(TEST_COLLECTION_NAME)

    exists = await memory.does_collection_exist(TEST_COLLECTION_NAME)
    assert not exists

    # Delete a non-existent collection with no error
    await memory.delete_collection(TEST_COLLECTION_NAME)


async def test_get_collections(memory_store):
    memory = memory_store

    collection_names = ["c1", "c2", "c3"]
    for c_n in collection_names:
        await memory.create_collection(c_n)

    names_from_func = await memory.get_collections()
    for c_n in collection_names:
        assert c_n in names_from_func
        await memory.delete_collection(c_n)


async def test_does_collection_exist(memory_store):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)
    exists = await memory.does_collection_exist(TEST_COLLECTION_NAME)
    assert exists

    await memory.delete_collection(TEST_COLLECTION_NAME)
    exists = await memory.does_collection_exist(TEST_COLLECTION_NAME)
    assert not exists


async def test_upsert_and_get(memory_store, memory_record1):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)

    # Insert a record
    await memory.upsert(TEST_COLLECTION_NAME, memory_record1)
    fetch_1 = await memory.get(TEST_COLLECTION_NAME, memory_record1._id, True)

    assert fetch_1 is not None, "Could not get record"
    assert fetch_1._id == memory_record1._id
    assert fetch_1._is_reference == memory_record1._is_reference
    assert fetch_1._external_source_name == memory_record1._external_source_name
    assert fetch_1._description == memory_record1._description
    assert fetch_1._text == memory_record1._text
    assert fetch_1._additional_metadata == memory_record1._additional_metadata
    for expected, actual in zip(fetch_1.embedding, memory_record1.embedding):
        assert expected == actual, "Did not retain correct embedding"

    # Update a record
    memory_record1._text = "updated sample text1"

    await memory.upsert(TEST_COLLECTION_NAME, memory_record1)
    fetch_1 = await memory.get(TEST_COLLECTION_NAME, memory_record1._id, True)

    assert fetch_1 is not None, "Could not get record"
    assert fetch_1._text == memory_record1._text, "Did not update record"


async def test_upsert_batch_and_get_batch(memory_store, memory_record1, memory_record2):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)

    ids = [memory_record1._id, memory_record2._id]
    await memory.upsert_batch(TEST_COLLECTION_NAME, [memory_record1, memory_record2])

    fetched = await memory.get_batch(TEST_COLLECTION_NAME, ids, True)

    assert len(fetched) > 0, "Could not get records"
    for f in fetched:
        assert f._id in ids


async def test_remove(memory_store, memory_record1):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)

    await memory.upsert(TEST_COLLECTION_NAME, memory_record1)
    await memory.remove(TEST_COLLECTION_NAME, memory_record1._id)
    get_record = await memory.get(TEST_COLLECTION_NAME, memory_record1._id, False)

    assert not get_record, "Record was not removed"


async def test_remove_batch(memory_store, memory_record1, memory_record2):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)

    ids = [memory_record1._id, memory_record2._id]
    await memory.upsert_batch(TEST_COLLECTION_NAME, [memory_record1, memory_record2])
    await memory.remove_batch(TEST_COLLECTION_NAME, ids)
    get_records = await memory.get_batch(TEST_COLLECTION_NAME, ids, False)

    assert len(get_records) == 0, "Records were not removed"


async def test_get_nearest_match(memory_store, memory_record1, memory_record2):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)

    await memory.upsert_batch(TEST_COLLECTION_NAME, [memory_record1, memory_record2])
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match(
        TEST_COLLECTION_NAME,
        test_embedding,
        min_relevance_score=0.0,
        with_embedding=True,
    )

    assert result is not None
    assert result[0]._id == memory_record1._id
    assert result[0]._is_reference == memory_record1._is_reference
    assert result[0]._external_source_name == memory_record1._external_source_name
    assert result[0]._description == memory_record1._description
    assert result[0]._text == memory_record1._text
    assert result[0]._additional_metadata == memory_record1._additional_metadata
    for i in range(len(result[0]._embedding)):
        assert result[0]._embedding[i] == memory_record1._embedding[i]


async def test_get_nearest_matches(memory_store, memory_record1, memory_record2, memory_record3):
    memory = memory_store

    await memory.create_collection(TEST_COLLECTION_NAME)

    await memory.upsert_batch(TEST_COLLECTION_NAME, [memory_record1, memory_record2, memory_record3])
    test_embedding = memory_record2.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.025

    result = await memory.get_nearest_matches(
        TEST_COLLECTION_NAME,
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )

    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
