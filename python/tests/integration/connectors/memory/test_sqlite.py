import os
from datetime import datetime
import logging

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.memory.sqlite import SQLiteMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import aiosqlite

    aiosqlite_installed = True
except ImportError:
    aiosqlite_installed = False

pytestmark = pytest.mark.skipif(
    not aiosqlite_installed, reason="aiosqlite is not installed"
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def sqlite_db_file():
    if "Python_Integration_Tests" in os.environ:
        file = os.environ["SQLITE_DB_FILE"]
    else:
        try:
            file = sk.sqlite_settings_from_dot_env()
        except Exception:
            file = "sqlite_test.db"
    if os.path.exists(file):
        os.remove(file)
    yield file
    if os.path.exists(file):
        os.remove(file)


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


@pytest.mark.asyncio
async def test_constructor(sqlite_db_file):
    store = SQLiteMemoryStore(sqlite_db_file, None)
    assert store is not None
    assert store._conn is None, "Connection should be None before connect() is called"
    await store.connect()
    assert (
        store._conn is not None
    ), "Connection should not be None after connect() is called"
    await store.close_async()


@pytest.mark.asyncio
async def test_async_context(sqlite_db_file):
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        assert store is not None
        assert (
            store._conn is not None
        ), "connect() should be automatically called in async context"


@pytest.mark.asyncio
async def test_create_and_does_collection_exist_async(sqlite_db_file):
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        result = await store.does_collection_exist_async("test_collection")
        assert result is False

        await store.create_collection_async("test_collection")
        result = await store.does_collection_exist_async("test_collection")
        assert result is True


@pytest.mark.asyncio
async def test_get_collections_async(sqlite_db_file):
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        await store.create_collection_async("test_collection")
        result = await store.get_collections_async()
        assert "test_collection" in result


@pytest.mark.asyncio
async def test_delete_collection_async(sqlite_db_file):
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        await store.create_collection_async("test_delete_collection")
        result = await store.get_collections_async()
        assert "test_delete_collection" in result

        await store.delete_collection_async("test_delete_collection")
        result = await store.get_collections_async()
        assert "test_delete_collection" not in result


@pytest.mark.asyncio
async def test_does_collection_exist_async(sqlite_db_file):
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        assert (
            await store.does_collection_exist_async("test_existence_collection")
            is False
        )
        await store.create_collection_async("test_existence_collection")
        assert (
            await store.does_collection_exist_async("test_existence_collection") is True
        )


@pytest.mark.asyncio
async def test_upsert_async_and_get_async(sqlite_db_file, memory_record1):
    collection = "test_upsert_collection"
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        await store.create_collection_async(collection)
        await store.upsert_async(collection, memory_record1)
        result = await store.get_async(collection, memory_record1._id, True)

        assert result is not None
        assert result._id == memory_record1._id
        assert result._text == memory_record1._text
        assert np.equal(result._embedding, memory_record1._embedding).all()
        assert result._timestamp == memory_record1._timestamp


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(
    sqlite_db_file, memory_record1, memory_record2
):
    collection = "test_upsert_batch_and_get_batch_collection"
    async with SQLiteMemoryStore(sqlite_db_file, logger) as store:
        await store.create_collection_async(collection)
        await store.upsert_batch_async(collection, [memory_record1, memory_record2])

        results = await store.get_batch_async(
            collection,
            [memory_record1._id, memory_record2._id],
            with_embeddings=True,
        )

        assert len(results) == 2
        assert results[0]._id in [memory_record1._id, memory_record2._id]
        assert results[1]._id in [memory_record1._id, memory_record2._id]
