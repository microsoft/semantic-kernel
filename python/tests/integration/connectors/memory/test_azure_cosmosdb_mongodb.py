import os
from datetime import datetime

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.memory.memory_record import MemoryRecord

from .mongodb_sample import MongoDBMemoryStore

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


@pytest.fixture(scope="session", params=["azuremongodb", "mongodbatlas"])
def connection(request):
    api_type = request.param
    if "Python_Integration_Tests" in os.environ:
        connection_string = os.environ["AZURE_COSMODB_MONGO_CONNECTION_STRING"]
    else:
        # Load credentials from .env file, or go to default if not found
        try:
            connection_string = sk.azure_cosmos_mongodb_settings_from_dot_env()
        except Exception:
            if api_type == "azuremongodb":
                connection_string = "azureconnectionstring"
            else:
                connection_string = "mongodbatlasconnectionstring"
    return connection_string, api_type


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
    )


@pytest.fixture
def memory_store(connection):
    # Setup and yield
    mongodb_mem_store = MongoDBMemoryStore(
        connection_string=connection[0],
        vector_size=TEST_VEC_SIZE,
        api_type=connection[1],
        collection_name=TEST_COLLECTION_NAME,
        database_name="test_db",
        embedding_key="embedding",
    )
    yield mongodb_mem_store

    # Delete test collection after test
    # asyncio.run(mongodb_mem_store.delete_collection_async(TEST_COLLECTION_NAME))


def test_constructor(memory_store):
    memory = memory_store
    assert memory


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
    fetch_1 = await memory.get_async(TEST_COLLECTION_NAME, memory_record1._id)

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

    await memory.upsert_async(TEST_COLLECTION_NAME, memory_record1)
    fetch_1 = await memory.get_async(TEST_COLLECTION_NAME, memory_record1._id)

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

    fetched = await memory.get_batch_async(TEST_COLLECTION_NAME, ids)

    assert len(fetched) > 0, "Could not get records"
    for f in fetched:
        assert f._id in ids


@pytest.mark.asyncio
async def test_remove_async(memory_store, memory_record1):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME)

    await memory.upsert_async(TEST_COLLECTION_NAME, memory_record1)
    await memory.remove_async(TEST_COLLECTION_NAME, memory_record1._id)
    get_record = await memory.get_async(TEST_COLLECTION_NAME, memory_record1._id)

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
    get_records = await memory.get_batch_async(TEST_COLLECTION_NAME, ids)

    assert len(get_records) == 0, "Records were not removed"


@pytest.mark.asyncio
async def test_get_nearest_match_async(memory_store, memory_record1, memory_record2):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME, num_lists=2)

    await memory.upsert_batch_async(
        TEST_COLLECTION_NAME, [memory_record1, memory_record2]
    )
    test_embedding = memory_record1.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match_async(TEST_COLLECTION_NAME, test_embedding)

    assert result is not None
    assert result._id == memory_record1._id
    assert result._is_reference == memory_record1._is_reference
    assert result._external_source_name == memory_record1._external_source_name
    assert result._description == memory_record1._description
    assert result._text == memory_record1._text
    assert result._additional_metadata == memory_record1._additional_metadata
    for i in range(len(result._embedding)):
        assert result._embedding[i] == memory_record1._embedding[i]


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    memory_store, memory_record1, memory_record2, memory_record3
):
    memory = memory_store

    await memory.create_collection_async(TEST_COLLECTION_NAME, num_lists=2)

    await memory.upsert_batch_async(
        TEST_COLLECTION_NAME, [memory_record1, memory_record2, memory_record3]
    )
    test_embedding = memory_record2.embedding.copy()
    test_embedding[0] = test_embedding[0] + 0.025

    result = await memory.get_nearest_matches_async(
        TEST_COLLECTION_NAME, test_embedding, limit=2
    )

    assert len(result) == 2
    assert result[0]._id in [memory_record3._id, memory_record2._id]
    assert result[1]._id in [memory_record3._id, memory_record2._id]
