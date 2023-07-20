# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime

import numpy as np
import pytest

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
    # TODO: figure out better configuration practice with env
    return "redis://localhost:6379"


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


def test_constructor(connection_string):
    memory = RedisMemoryStore(connection_string)
    assert memory._database.ping()


def test_configure(connection_string):
    memory = RedisMemoryStore(connection_string)

    # Test current port
    port_setup = memory._database.config_get("port")
    memory.configure(port_setup)
    assert memory._database.ping()

    # Test faulty port
    port_setup["port"] = "not_number"
    try:
        memory.configure(port_setup)
    except redis.exceptions.ResponseError:
        pass
    assert memory._database.ping()


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

    await memory.create_collection_async("test_collection")
    await memory.upsert_async("test_collection", memory_record1)

    fetch_1 = await memory.get_async("test_collection", "test_id1", True)
    assert fetch_1._id == "test_id1"

    for expected, actual in zip(fetch_1.embedding, memory_record1.embedding):
        assert expected == actual, "Did not retain correct embedding"


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(
    connection_string, memory_record1, memory_record2
):
    memory = RedisMemoryStore(connection_string)

    await memory.create_collection_async("test_collection")
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])

    fetched = await memory.get_batch_async(
        "test_collection", ["test_id1", "test_id2"], True
    )

    assert fetched[0]._id == "test_id1"
    for expected, actual in zip(fetched[0].embedding, memory_record1.embedding):
        assert expected == actual, "Did not retain correct embedding"

    assert fetched[1]._id == "test_id2"
    for expected, actual in zip(fetched[1].embedding, memory_record2.embedding):
        assert expected == actual, "Did not retain correct embedding"


@pytest.mark.asyncio
async def test_remove_async(connection_string, memory_record1):
    pass


@pytest.mark.asyncio
async def test_remove_batch_async(connection_string, memory_record1, memory_record2):
    pass


@pytest.mark.asyncio
async def test_get_nearest_match_async(
    connection_string, memory_record1, memory_record2
):
    pass


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    connection_string, memory_record1, memory_record2, memory_record3
):
    pass
