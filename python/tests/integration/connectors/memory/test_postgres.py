# Copyright (c) Microsoft. All rights reserved.

import os
from datetime import datetime

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.memory.postgres import PostgresMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import psycopg  # noqa: F401

    psycopg_installed = True
except ImportError:
    psycopg_installed = False

pytestmark = pytest.mark.skipif(
    not psycopg_installed, reason="psycopg is not installed"
)

try:
    import psycopg_pool  # noqa: F401

    psycopg_pool_installed = True
except ImportError:
    psycopg_pool_installed = False

pytestmark = pytest.mark.skipif(
    not psycopg_pool_installed, reason="psycopg_pool is not installed"
)


@pytest.fixture(scope="session")
def get_postgres_config():
    if "Python_Integration_Tests" in os.environ:
        connection_string = os.environ["Postgres__ApiKey"]
    else:
        # Load credentials from .env file
        connection_string = sk.postgres_settings_from_dot_env()

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
        timestamp=str(datetime.now()),
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
        timestamp=str(datetime.now()),
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
        timestamp=str(datetime.now()),
    )


def test_constructor(get_postgres_config):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)
    assert memory._connection_pool is not None


@pytest.mark.asyncio
async def test_create_and_does_collection_exist_async(get_postgres_config):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    result = await memory.does_collection_exist_async("test_collection")
    assert result is not None


@pytest.mark.asyncio
async def test_get_collections_async(get_postgres_config):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    result = await memory.get_collections_async()
    assert "test_collection" in result


@pytest.mark.asyncio
async def test_delete_collection_async(get_postgres_config):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)

    result = await memory.get_collections_async()
    assert "test_collection" in result

    await memory.delete_collection_async("test_collection")
    result = await memory.get_collections_async()
    assert "test_collection" not in result


@pytest.mark.asyncio
async def test_does_collection_exist_async(get_postgres_config):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    result = await memory.does_collection_exist_async("test_collection")
    assert result is True


@pytest.mark.asyncio
async def test_upsert_async_and_get_async(get_postgres_config, memory_record1):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    await memory.upsert_async("test_collection", memory_record1)
    result = await memory.get_async(
        "test_collection", memory_record1._id, with_embedding=True
    )
    assert result is not None
    assert result._id == memory_record1._id
    assert result._text == memory_record1._text
    for i in range(len(result._embedding)):
        assert result._embedding[i] == memory_record1._embedding[i]


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(
    get_postgres_config, memory_record1, memory_record2
):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])

    results = await memory.get_batch_async(
        "test_collection",
        [memory_record1._id, memory_record2._id],
        with_embeddings=True,
    )

    assert len(results) == 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


@pytest.mark.asyncio
async def test_remove_async(get_postgres_config, memory_record1):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    await memory.upsert_async("test_collection", memory_record1)
    await memory.remove_async("test_collection", memory_record1._id)
    with pytest.raises(KeyError):
        _ = await memory.get_async(
            "test_collection", memory_record1._id, with_embedding=True
        )


@pytest.mark.asyncio
async def test_remove_batch_async(get_postgres_config, memory_record1, memory_record2):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])
    await memory.remove_batch_async(
        "test_collection", [memory_record1._id, memory_record2._id]
    )
    with pytest.raises(KeyError):
        _ = await memory.get_async(
            "test_collection", memory_record1._id, with_embedding=True
        )

    with pytest.raises(KeyError):
        _ = await memory.get_async(
            "test_collection", memory_record2._id, with_embedding=True
        )


@pytest.mark.asyncio
async def test_get_nearest_match_async(
    get_postgres_config, memory_record1, memory_record2
):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    await memory.upsert_batch_async("test_collection", [memory_record1, memory_record2])
    test_embedding = memory_record1.embedding
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match_async(
        "test_collection", test_embedding, min_relevance_score=0.0, with_embedding=True
    )
    assert result is not None
    assert result[0]._id == memory_record1._id


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    get_postgres_config, memory_record1, memory_record2, memory_record3
):
    connection_string = get_postgres_config
    memory = PostgresMemoryStore(connection_string, 1, 5)

    await memory.create_collection_async("test_collection", 2)
    await memory.upsert_batch_async(
        "test_collection", [memory_record1, memory_record2, memory_record3]
    )
    test_embedding = memory_record2.embedding
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
