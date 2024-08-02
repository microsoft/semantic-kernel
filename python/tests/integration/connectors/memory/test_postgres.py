# Copyright (c) Microsoft. All rights reserved.

import time

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.memory.postgres import PostgresMemoryStore
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings
from semantic_kernel.exceptions import ServiceResourceNotFoundError

try:
    import psycopg  # noqa: F401

    psycopg_installed = True
except ImportError:
    psycopg_installed = False

pytestmark = pytest.mark.skipif(not psycopg_installed, reason="psycopg is not installed")

try:
    import psycopg_pool  # noqa: F401

    psycopg_pool_installed = True
except ImportError:
    psycopg_pool_installed = False

pytestmark = pytest.mark.skipif(not psycopg_pool_installed, reason="psycopg_pool is not installed")


# Needed because the test service may not support a high volume of requests
@pytest.fixture(scope="module")
def wait_between_tests():
    time.sleep(0.5)
    return 0


@pytest.fixture(scope="session")
def connection_string():
    try:
        postgres_settings = PostgresSettings.create()
        return postgres_settings.connection_string.get_secret_value()
    except ValidationError:
        pytest.skip("Postgres Connection string not found in env vars.")


def test_constructor(connection_string):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)
    assert memory._connection_pool is not None


@pytest.mark.asyncio
async def test_create_and_does_collection_exist(connection_string):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    result = await memory.does_collection_exist("test_collection")
    assert result is not None


@pytest.mark.asyncio
async def test_get_collections(connection_string):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    result = await memory.get_collections()
    assert "test_collection" in result


@pytest.mark.asyncio
async def test_delete_collection(connection_string):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")

    result = await memory.get_collections()
    assert "test_collection" in result

    await memory.delete_collection("test_collection")
    result = await memory.get_collections()
    assert "test_collection" not in result


@pytest.mark.asyncio
async def test_does_collection_exist(connection_string):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    result = await memory.does_collection_exist("test_collection")
    assert result is True


@pytest.mark.asyncio
async def test_upsert_and_get(connection_string, memory_record1):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    await memory.upsert("test_collection", memory_record1)
    result = await memory.get("test_collection", memory_record1._id, with_embedding=True)
    assert result is not None
    assert result._id == memory_record1._id
    assert result._text == memory_record1._text
    assert result._timestamp == memory_record1._timestamp
    for i in range(len(result._embedding)):
        assert result._embedding[i] == memory_record1._embedding[i]


@pytest.mark.xfail(reason="Test failing with reason couldn't: get a connection after 30.00 sec")
@pytest.mark.asyncio
async def test_upsert_batch_and_get_batch(connection_string, memory_record1, memory_record2):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])

    results = await memory.get_batch(
        "test_collection",
        [memory_record1._id, memory_record2._id],
        with_embeddings=True,
    )

    assert len(results) == 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


@pytest.mark.xfail(reason="Test failing with reason couldn't: get a connection after 30.00 sec")
@pytest.mark.asyncio
async def test_remove(connection_string, memory_record1):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    await memory.upsert("test_collection", memory_record1)

    result = await memory.get("test_collection", memory_record1._id, with_embedding=True)
    assert result is not None

    await memory.remove("test_collection", memory_record1._id)
    with pytest.raises(ServiceResourceNotFoundError):
        _ = await memory.get("test_collection", memory_record1._id, with_embedding=True)


@pytest.mark.xfail(reason="Test failing with reason couldn't: get a connection after 30.00 sec")
@pytest.mark.asyncio
async def test_remove_batch(connection_string, memory_record1, memory_record2):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])
    await memory.remove_batch("test_collection", [memory_record1._id, memory_record2._id])
    with pytest.raises(ServiceResourceNotFoundError):
        _ = await memory.get("test_collection", memory_record1._id, with_embedding=True)

    with pytest.raises(ServiceResourceNotFoundError):
        _ = await memory.get("test_collection", memory_record2._id, with_embedding=True)


@pytest.mark.xfail(reason="Test failing with reason couldn't: get a connection after 30.00 sec")
@pytest.mark.asyncio
async def test_get_nearest_match(connection_string, memory_record1, memory_record2):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
    )
    assert result is not None
    assert result[0]._id == memory_record1._id
    assert result[0]._text == memory_record1._text
    assert result[0]._timestamp == memory_record1._timestamp
    for i in range(len(result[0]._embedding)):
        assert result[0]._embedding[i] == memory_record1._embedding[i]


@pytest.mark.asyncio
@pytest.mark.xfail(reason="The test is failing due to a timeout.")
async def test_get_nearest_matches(connection_string, memory_record1, memory_record2, memory_record3):
    memory = PostgresMemoryStore(connection_string, 2, 1, 5)

    await memory.create_collection("test_collection")
    await memory.upsert_batch("test_collection", [memory_record1, memory_record2, memory_record3])
    test_embedding = memory_record2.embedding
    test_embedding[0] = test_embedding[0] + 0.025

    result = await memory.get_nearest_matches(
        "test_collection",
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )
    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
