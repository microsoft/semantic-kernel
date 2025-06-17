# Copyright (c) Microsoft. All rights reserved.

import uuid
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated, Any

import pandas as pd
import pytest
import pytest_asyncio
from pydantic import BaseModel

from semantic_kernel.connectors.postgres import PostgresCollection, PostgresSettings, PostgresStore
from semantic_kernel.data.vector import (
    DistanceFunction,
    IndexKind,
    VectorStoreCollectionDefinition,
    VectorStoreField,
    vectorstoremodel,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorConnectionException,
    MemoryConnectorInitializationError,
)

try:
    import psycopg  # noqa: F401
    import psycopg_pool  # noqa: F401

    psycopg_pool_installed = True
except ImportError:
    psycopg_pool_installed = False

pg_settings: PostgresSettings = PostgresSettings()
try:
    connection_params_present = any(pg_settings.get_connection_args().values())
except MemoryConnectorInitializationError:
    connection_params_present = False

pytestmark = pytest.mark.skipif(
    not (psycopg_pool_installed or connection_params_present),
    reason="psycopg_pool is not installed" if not psycopg_pool_installed else "No connection parameters provided",
)


@vectorstoremodel
class SimpleDataModel(BaseModel):
    id: Annotated[int, VectorStoreField("key")]
    embedding: Annotated[
        list[float] | str | None,
        VectorStoreField(
            "vector",
            index_kind=IndexKind.HNSW,
            dimensions=3,
            distance_function=DistanceFunction.COSINE_SIMILARITY,
        ),
    ] = None
    data: Annotated[
        dict[str, Any],
        VectorStoreField("data", type="JSONB"),
    ]

    def model_post_init(self, context: Any) -> None:
        if self.embedding is None:
            self.embedding = self.data


def DataModelPandas(record) -> tuple:
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField(
                "vector",
                name="embedding",
                index_kind="hnsw",
                dimensions=3,
                distance_function="cosine_similarity",
                type="float",
            ),
            VectorStoreField("key", name="id", type="int"),
            VectorStoreField("data", name="data", type="dict"),
        ],
        container_mode=True,
        to_dict=lambda x: x.to_dict(orient="records"),
        from_dict=lambda x, **_: pd.DataFrame(x),
    )
    df = pd.DataFrame([record])
    return definition, df


@pytest_asyncio.fixture
async def vector_store() -> AsyncGenerator[PostgresStore, None]:
    try:
        async with await pg_settings.create_connection_pool() as pool:
            yield PostgresStore(connection_pool=pool)
    except MemoryConnectorConnectionException:
        pytest.skip("Postgres connection not available")
        yield None
        return


@asynccontextmanager
async def create_simple_collection(
    vector_store: PostgresStore,
) -> AsyncGenerator[PostgresCollection[int, SimpleDataModel], None]:
    """Returns a collection with a unique name that is deleted after the context.

    This can be moved to use a fixture with scope=function and loop_scope=session
    after upgrade to pytest-asyncio 0.24. With the current version, the fixture
    would both cache and use the event loop of the declared scope.
    """
    suffix = str(uuid.uuid4()).replace("-", "")[:8]
    collection_id = f"test_collection_{suffix}"
    collection = vector_store.get_collection(collection_name=collection_id, record_type=SimpleDataModel)
    assert isinstance(collection, PostgresCollection)
    await collection.ensure_collection_exists()
    try:
        yield collection
    finally:
        await collection.ensure_collection_deleted()


def test_create_store(vector_store):
    assert vector_store is not None
    assert vector_store.connection_pool is not None


async def test_ensure_collection_exists_exists_and_delete(vector_store: PostgresStore):
    suffix = str(uuid.uuid4()).replace("-", "")[:8]

    collection = vector_store.get_collection(collection_name=f"test_collection_{suffix}", record_type=SimpleDataModel)

    does_exist_1 = await collection.collection_exists()
    assert does_exist_1 is False

    await collection.ensure_collection_exists()
    does_exist_2 = await collection.collection_exists()
    assert does_exist_2 is True

    await collection.ensure_collection_deleted()
    does_exist_3 = await collection.collection_exists()
    assert does_exist_3 is False


async def test_list_collection_names(vector_store):
    async with create_simple_collection(vector_store) as simple_collection:
        simple_collection_id = simple_collection.collection_name
        result = await vector_store.list_collection_names()
        assert simple_collection_id in result


async def test_upsert_get_and_delete(vector_store: PostgresStore):
    record = SimpleDataModel(id=1, embedding=[1.1, 2.2, 3.3], data={"key": "value"})
    async with create_simple_collection(vector_store) as simple_collection:
        result_before_upsert = await simple_collection.get(1)
        assert result_before_upsert is None

        await simple_collection.upsert(record)
        result = await simple_collection.get(1)
        assert result is not None
        assert result.id == record.id
        assert result.embedding == record.embedding
        assert result.data == record.data

        # Check that the table has an index
        connection_pool = simple_collection.connection_pool
        async with connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT indexname FROM pg_indexes WHERE tablename = %s", (simple_collection.collection_name,)
            )
            rows = await cur.fetchall()
            index_names = [index[0] for index in rows]
            assert any("embedding_idx" in index_name for index_name in index_names)

        await simple_collection.delete(1)
        result_after_delete = await simple_collection.get(1)
        assert result_after_delete is None


async def test_upsert_get_and_delete_pandas(vector_store):
    record = SimpleDataModel(id=1, embedding=[1.1, 2.2, 3.3], data={"key": "value"})
    definition, df = DataModelPandas(record.model_dump())

    suffix = str(uuid.uuid4()).replace("-", "")[:8]
    collection = vector_store.get_collection(
        collection_name=f"test_collection_{suffix}",
        record_type=pd.DataFrame,
        definition=definition,
    )
    await collection.ensure_collection_exists()

    try:
        result_before_upsert = await collection.get(1)
        assert result_before_upsert is None

        await collection.upsert(df)
        result: pd.DataFrame = await collection.get(1)
        assert result is not None
        row = result.iloc[0]
        assert row.id == record.id
        assert row.embedding == record.embedding
        assert row.data == record.data

        await collection.delete(1)
        result_after_delete = await collection.get(1)
        assert result_after_delete is None
    finally:
        await collection.ensure_collection_deleted()


async def test_upsert_get_and_delete_multiple(vector_store: PostgresStore):
    async with create_simple_collection(vector_store) as simple_collection:
        record1 = SimpleDataModel(id=1, embedding=[1.1, 2.2, 3.3], data={"key": "value"})
        record2 = SimpleDataModel(id=2, embedding=[4.4, 5.5, 6.6], data={"key": "value"})

        result_before_upsert = await simple_collection.get([1, 2])
        assert result_before_upsert is None

        await simple_collection.upsert([record1, record2])
        # Test get for the two existing keys and one non-existing key;
        # this should return only the two existing records.
        result = await simple_collection.get([1, 2, 3])
        assert result is not None
        assert isinstance(result, Sequence)
        assert len(result) == 2
        assert result[0] is not None
        assert result[0].id == record1.id
        assert result[0].embedding == record1.embedding
        assert result[0].data == record1.data
        assert result[1] is not None
        assert result[1].id == record2.id
        assert result[1].embedding == record2.embedding
        assert result[1].data == record2.data

        await simple_collection.delete([1, 2])
        result_after_delete = await simple_collection.get([1, 2])
        assert result_after_delete is None


async def test_search(vector_store: PostgresStore):
    async with create_simple_collection(vector_store) as simple_collection:
        records = [
            SimpleDataModel(id=1, embedding=[1.0, 0.0, 0.0], data={"key": "value1"}),
            SimpleDataModel(id=2, embedding=[0.8, 0.2, 0.0], data={"key": "value2"}),
            SimpleDataModel(id=3, embedding=[0.6, 0.0, 0.4], data={"key": "value3"}),
            SimpleDataModel(id=4, embedding=[1.0, 1.0, 0.0], data={"key": "value4"}),
            SimpleDataModel(id=5, embedding=[0.0, 1.0, 1.0], data={"key": "value5"}),
            SimpleDataModel(id=6, embedding=[1.0, 0.0, 1.0], data={"key": "value6"}),
        ]

        await simple_collection.upsert(records)

        try:
            search_results = await simple_collection.search(vector=[1.0, 0.0, 0.0], top=3, include_total_count=True)
            assert search_results is not None
            assert search_results.total_count == 3
            assert {result.record.id async for result in search_results.results} == {1, 2, 3}

        finally:
            await simple_collection.delete([r.id for r in records])
