import asyncio
import os
from datetime import datetime

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.memory.azure_cosmosdb_mongodb import (
    AzureCosmosDbMongoDBMemoryStore,
)
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import pymongo  # noqa: F401

    pymongo_installed = True
    TEST_COLLECTION_NAME = "test_collection"
    TEST_VEC_SIZE = 2
except ImportError:
    pymongo_installed = False

pytestmark = pytest.mark.skipif(
    not pymongo_installed, reason="PyMongo is not installed"
)


@pytest.fixture(scope="session")
def connection_string():
    if "Python_Integration_Tests" in os.environ:
        connection_string = os.environ["AZURE_COSMODB_MONGO_CONNECTION_STRING"]
    else:
        # Load credentials from .env file, or go to default if not found
        try:
            connection_string = sk.azure_cosmos_mongodb_settings_from_dot_env()
        except Exception:
            connection_string = ""

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


@pytest.fixture
def memory_store(connection_string):
    # Setup and yield
    azurecosmos_mongodb_mem_store = AzureCosmosDbMongoDBMemoryStore(
        connection_string,
        vector_size=TEST_VEC_SIZE,
        database_name="test_db",
        embedding_key="embedding",
    )
    yield azurecosmos_mongodb_mem_store

    # Delete test collection after test
    asyncio.run(
        azurecosmos_mongodb_mem_store.delete_collection_async(TEST_COLLECTION_NAME)
    )


def test_constructor(memory_store):
    memory = memory_store
    assert memory and memory._database.ping()


@pytest.mark.asyncio
async def test_create_and_does_collection_exist_async(memory_store):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)
    exists = await memory.does_collection_exist_async(TEST_COLLECTION_NAME)
    assert exists


@pytest.mark.asyncio
async def test_delete_collection_async(memory_store):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)
    await memory.delete_collection_async(TEST_COLLECTION_NAME)

    exists = await memory.does_collection_exist_async(TEST_COLLECTION_NAME)
    assert not exists

    # Delete a non-existent collection with no error
    await memory.delete_collection_async(TEST_COLLECTION_NAME)


@pytest.mark.asyncio
async def test_get_collections_async(memory_store):
    memory = memory_store

    collection_names = ["c1", "c2", "c3"]
    for c_n in collection_names:
        await memory.create_collection_async(c_n)

    names_from_func = await memory.get_collections_async()
    for c_n in collection_names:
        assert c_n in names_from_func
        await memory.delete_collection_async(c_n)


@pytest.mark.asyncio
async def test_does_collection_exist_async(memory_store):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)
    exists = await memory.does_collection_exist_async(TEST_COLLECTION_NAME)
    assert exists

    await memory.delete_collection_async(TEST_COLLECTION_NAME)
    exists = await memory.does_collection_exist_async(TEST_COLLECTION_NAME)
    assert not exists


@pytest.mark.asyncio
async def test_upsert_async_and_get_async(memory_store, memory_record1):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    # Insert a record
    await memory.upsert_async(TEST_COLLECTION_NAME, memory_record1)
    fetch_1 = await memory.get_async(TEST_COLLECTION_NAME, memory_record1._id, True)

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
    memory_record1._text = "updated sample text1"

    await memory.upsert_async(TEST_COLLECTION_NAME, memory_record1)
    fetch_1 = await memory.get_async(TEST_COLLECTION_NAME, memory_record1._id, True)

    assert fetch_1 is not None, "Could not get record"
    assert fetch_1._text == memory_record1._text, "Did not update record"


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(
    memory_store, memory_record1, memory_record2
):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    ids = [memory_record1._id, memory_record2._id]
    await memory.upsert_batch_async(
        TEST_COLLECTION_NAME, [memory_record1, memory_record2]
    )

    fetched = await memory.get_batch_async(TEST_COLLECTION_NAME, ids, True)

    assert len(fetched) > 0, "Could not get records"
    for f in fetched:
        assert f._id in ids


@pytest.mark.asyncio
async def test_remove_async(memory_store, memory_record1):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    await memory.upsert_async(TEST_COLLECTION_NAME, memory_record1)
    await memory.remove_async(TEST_COLLECTION_NAME, memory_record1._id)
    get_record = await memory.get_async(TEST_COLLECTION_NAME, memory_record1._id, False)

    assert not get_record, "Record was not removed"


@pytest.mark.asyncio
async def test_remove_batch_async(memory_store, memory_record1, memory_record2):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    ids = [memory_record1._id, memory_record2._id]
    await memory.upsert_batch_async(
        TEST_COLLECTION_NAME, [memory_record1, memory_record2]
    )
    await memory.remove_batch_async(TEST_COLLECTION_NAME, ids)
    get_records = await memory.get_batch_async(TEST_COLLECTION_NAME, ids, False)

    assert len(get_records) == 0, "Records were not removed"


@pytest.mark.asyncio
async def test_get_nearest_match_async(memory_store, memory_record1, memory_record2):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    await memory.upsert_batch_async(
        TEST_COLLECTION_NAME, [memory_record1, memory_record2]
    )
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match_async(
        TEST_COLLECTION_NAME,
        test_embedding,
        min_relevance_score=0.0,
        with_embedding=True,
    )

    assert result is not None
    assert result[0]._id == memory_record1._id
    assert result[0]._timestamp == memory_record1._timestamp
    assert result[0]._is_reference == memory_record1._is_reference
    assert result[0]._external_source_name == memory_record1._external_source_name
    assert result[0]._description == memory_record1._description
    assert result[0]._text == memory_record1._text
    assert result[0]._additional_metadata == memory_record1._additional_metadata
    for i in range(len(result[0]._embedding)):
        assert result[0]._embedding[i] == memory_record1._embedding[i]


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    memory_store, memory_record1, memory_record2, memory_record3
):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    await memory.upsert_batch_async(
        TEST_COLLECTION_NAME, [memory_record1, memory_record2, memory_record3]
    )
    test_embedding = memory_record2.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.025

    result = await memory.get_nearest_matches_async(
        TEST_COLLECTION_NAME,
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )

    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
