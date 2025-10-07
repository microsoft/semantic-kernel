# Copyright (c) 2025, Oracle Corporation. All rights reserved.

from array import array
from dataclasses import dataclass
from typing import Annotated
from unittest.mock import AsyncMock, MagicMock

import oracledb
import pandas as pd
import pytest
import pytest_asyncio

from semantic_kernel.connectors.oracle import OracleCollection, OracleStore
from semantic_kernel.data.vector import (
    DistanceFunction,
    IndexKind,
    VectorStoreCollectionDefinition,
    VectorStoreField,
    vectorstoremodel,
)


@vectorstoremodel
@dataclass
class SimpleModel:
    id: Annotated[int, VectorStoreField("key")]
    vector: Annotated[
        list[float] | None,
        VectorStoreField(
            "vector",
            type="float",
            dimensions=3,
            index_kind=IndexKind.HNSW,
            distance_function=DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE,
        ),
    ] = None


def PandasDataframeModel(record) -> tuple:
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="int"),
            VectorStoreField(
                "vector",
                name="embedding",
                type="float32",
                dimensions=5,
                distance_function=DistanceFunction.COSINE_DISTANCE,
                index_kind=IndexKind.IVF_FLAT
            ),
        ],
        to_dict=lambda record, **_: record.to_dict(orient="records"),
        from_dict=lambda records, **_: pd.DataFrame(records),
        container_mode=True,
    )
    df = (
        pd.DataFrame([record])
        if isinstance(record, dict)
        else pd.DataFrame(record)
    )
    return definition, df


@pytest_asyncio.fixture
async def mock_connection_pool():
    mock_conn = AsyncMock()
    mock_conn.fetchall = AsyncMock(return_value=[("COLL1",), ("COLL2",)])

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_conn
    mock_context_manager.__aexit__.return_value = None

    pool = MagicMock(spec=oracledb.AsyncConnectionPool)
    pool.acquire.return_value = mock_context_manager

    return pool


@pytest_asyncio.fixture
async def oracle_store(mock_connection_pool):
    return OracleStore(
        connection_pool=mock_connection_pool,
        db_schema="MY_SCHEMA",
    )


@pytest.mark.asyncio
async def test_list_collection_names_with_schema(oracle_store):
    names = await oracle_store.list_collection_names()
    assert names == ["COLL1", "COLL2"]


def test_get_collection_returns_oracle_collection(oracle_store):
    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="TEST",
    )
    assert isinstance(collection, OracleCollection)
    assert collection.collection_name == "TEST"
    assert collection.db_schema == "MY_SCHEMA"


@pytest.mark.asyncio
async def test_collection_exists_true(oracle_store, mock_connection_pool):
    conn = AsyncMock()
    conn.fetchone = AsyncMock(return_value=(1,))
    mock_connection_pool.acquire.return_value.__aenter__.return_value = conn

    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="EXISTING",
    )
    result = await collection.collection_exists()
    assert result is True


@pytest.mark.asyncio
async def test_collection_exists_false(oracle_store, mock_connection_pool):
    conn = AsyncMock()
    conn.fetchone = AsyncMock(return_value=None)
    mock_connection_pool.acquire.return_value.__aenter__.return_value = conn

    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="MISSING",
    )
    result = await collection.collection_exists()
    assert result is False


@pytest.mark.asyncio
async def test_ensure_collection_exists_creates_when_missing(
    oracle_store, mock_connection_pool
):
    conn = AsyncMock()
    conn.fetchone = AsyncMock(return_value=False)
    mock_connection_pool.acquire.return_value.__aenter__.return_value = conn
    collection = oracle_store.get_collection(
        SimpleModel, collection_name="NEW"
    )
    await collection.ensure_collection_exists()
    conn.execute.assert_called()


@pytest.mark.asyncio
async def test_create_table_with_get_collection(
    oracle_store, mock_connection_pool
):
    mock_conn = AsyncMock()
    mock_connection_pool.acquire.return_value.__aenter__.return_value = (
        mock_conn
    )

    collection = oracle_store.get_collection(
        SimpleModel, collection_name="MY_COLLECTION"
    )

    await collection.ensure_collection_exists()

    mock_conn.execute.assert_awaited()
    sql_statements = [
        args[0].lower()
        for name, args, _ in mock_conn.mock_calls
        if name == "execute"
    ]
    assert any("create table" in sql for sql in sql_statements)
    assert any("my_collection" in sql for sql in sql_statements)
    assert any("vector(3 , float64)" in sql for sql in sql_statements)

    mock_conn.commit.assert_called_once()


@pytest.mark.asyncio
async def test_pandasDataframe_with_get_collection(
    oracle_store, mock_connection_pool
):
    mock_conn = AsyncMock()
    mock_connection_pool.acquire.return_value.__aenter__.return_value = (
        mock_conn
    )

    records = {
        "id": 1,
        "embedding": [1.1, 2.2, 3.3],
        }

    definition, _ = PandasDataframeModel(records)

    collection = oracle_store.get_collection(
        collection_name="MY_COLLECTION",
        record_type=pd.DataFrame,
        definition=definition,
    )
    await collection.ensure_collection_exists()

    mock_conn.execute.assert_awaited()
    sql_statements = [
        args[0].lower()
        for name, args, _ in mock_conn.mock_calls
        if name == "execute"
    ]

    assert any("create table" in sql for sql in sql_statements)
    assert any("my_collection" in sql for sql in sql_statements)
    assert any("vector(5 , float32)" in sql for sql in sql_statements)

    mock_conn.commit.assert_called_once()


@pytest.mark.asyncio
async def test_index_creation_distance_with_get_collection(
    oracle_store, mock_connection_pool
):
    mock_conn = AsyncMock()
    mock_connection_pool.acquire.return_value.__aenter__.return_value = (
        mock_conn
    )

    collection = oracle_store.get_collection(
        SimpleModel, collection_name="COLLECTION_WITH_INDEX"
    )

    await collection.ensure_collection_exists()

    mock_conn.execute.assert_awaited()
    called_sql = mock_conn.execute.call_args[0][0].lower()

    assert "create vector index" in called_sql
    assert "collection_with_index_vector_idx" in called_sql
    assert "inmemory neighbor graph" in called_sql
    assert "distance euclidean_squared" in called_sql

    mock_conn.commit.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_collection_deleted(oracle_store, mock_connection_pool):
    conn = AsyncMock()
    conn.fetchone = AsyncMock(return_value=(1,))
    mock_connection_pool.acquire.return_value.__aenter__.return_value = conn

    collection = oracle_store.get_collection(
        SimpleModel, collection_name="TO_DELETE"
    )

    await collection.ensure_collection_exists()
    await collection.ensure_collection_deleted()

    assert any(
        "DROP TABLE" in str(call.args[0])
        for call in conn.execute.call_args_list
    )


@pytest.mark.asyncio
async def test_upsert(oracle_store, mock_connection_pool):
    mock_conn = AsyncMock()
    mock_connection_pool.acquire.return_value.__aenter__.return_value = (
        mock_conn
    )

    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="MY_COLLECTION"
    )

    await collection.ensure_collection_exists()
    await collection.upsert(SimpleModel(id=1, vector=[0.1, 0.2, 0.3]))

    mock_conn.executemany.assert_called_once()

    merge_sql, params = mock_conn.executemany.call_args[0]

    assert merge_sql.startswith('MERGE INTO "MY_SCHEMA"."MY_COLLECTION"')
    assert "UPDATE SET t.\"vector\"" in merge_sql
    assert "WHEN NOT MATCHED THEN" in merge_sql
    assert "INSERT (\"id\", \"vector\")" in merge_sql

    expected_param = (1, array("d", [0.1, 0.2, 0.3]))
    assert params[0] == expected_param
    assert mock_conn.commit.call_count == 2


@pytest.mark.asyncio
async def test_get_with_include_vectors(oracle_store, mock_connection_pool):
    mock_conn = AsyncMock()
    mock_conn.description = [("id",), ("vector",)]
    mock_connection_pool.acquire.return_value.__aenter__.return_value = (
        mock_conn
    )

    collection = oracle_store.get_collection(
        SimpleModel, collection_name="MY_COLLECTION"
    )

    await collection.ensure_collection_exists()
    await collection.upsert(SimpleModel(id=1, vector=[0.1, 0.2, 0.3]))

    mock_conn.fetchall.return_value = [(1, [0.1, 0.2, 0.3])]
    results = await collection.get([1], include_vectors=True)
    assert results.id == 1
    assert results.vector == [0.1, 0.2, 0.3]

    executed_sql = [args[0] for args, _ in mock_conn.fetchall.call_args_list]
    assert any(
        'SELECT "id" AS "id", "vector" AS "vector"' in sql
        for sql in executed_sql
    ), "Expected vector column to be selected when include_vectors=True"

    mock_conn.fetchall.reset_mock()
    mock_conn.fetchall.return_value = [(1, None)]
    results = await collection.get([1], include_vectors=False)
    assert results.id == 1
    assert results.vector is None

    executed_sql = [args[0] for args, _ in mock_conn.fetchall.call_args_list]
    assert any(
        'SELECT "id" AS "id", "vector" AS "vector"' not in sql
        for sql in executed_sql
    ), "Vector column should not be selected when include_vectors=False"


@pytest.mark.asyncio
async def test_upsert_and_get(oracle_store, mock_connection_pool):
    conn = AsyncMock()
    conn.description = [("id",), ("vector",)]
    conn.fetchall = AsyncMock(return_value=[(1, [0.1, 0.2, 0.3])])

    mock_connection_pool.acquire.return_value.__aenter__.return_value = conn

    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="TEST"
    )

    await collection.ensure_collection_exists()
    await collection.upsert(SimpleModel(id=1, vector=[0.1, 0.2, 0.3]))
    assert (
        conn.executemany.await_count >= 1 or conn.execute.await_count >= 1
    ), "Expected upsert to call executemany() or execute()"

    results = await collection.get([1], include_vectors=True)

    assert results.id == 1
    assert results.vector == [0.1, 0.2, 0.3]
    conn.fetchall.assert_awaited_once()
    conn.fetchall.reset_mock()
    conn.fetchall.return_value = [(1, None)]
    conn.description = [("id",)]

    results = await collection.get([1], include_vectors=False)
    assert results.id == 1
    assert results.vector is None


@pytest.mark.asyncio
async def test_delete_record(oracle_store, mock_connection_pool):
    conn = AsyncMock()
    mock_connection_pool.acquire.return_value.__aenter__.return_value = conn

    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="MY_COLLECTION",
    )

    await collection.ensure_collection_exists()
    await collection.delete([1])
    conn.executemany.assert_awaited()
    called_sql = conn.executemany.call_args[0][0].lower()
    assert "delete" in called_sql
    assert "my_collection" in called_sql


@pytest.mark.asyncio
async def test_search(oracle_store, mock_connection_pool):
    mock_cursor = MagicMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[(1, [0.1, 0.2, 0.3])])
    mock_cursor.description = [("id",), ("vector",)]

    mock_cursor_cm = MagicMock()
    mock_cursor_cm.__enter__.return_value = mock_cursor
    mock_cursor_cm.__exit__.return_value = None

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.commit = AsyncMock()
    mock_conn.inputtypehandler = None
    mock_conn.cursor = MagicMock(return_value=mock_cursor_cm)

    class MockAcquire:
        def __init__(self, conn):
            self._conn = conn

        def __await__(self):
            async def _():
                return self
            return _().__await__()

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    mock_connection_pool.acquire = MagicMock(
        return_value=MockAcquire(mock_conn)
    )

    collection = oracle_store.get_collection(
        SimpleModel,
        collection_name="MY_COLLECTION",
    )

    await collection.ensure_collection_exists()

    results = await collection.search(
        vector_property_name="vector",
        vector=[0.1, 0.2, 0.3],
        top=1,
        filter=lambda x: x.id == [1, 7, 9],
        include_total_count=True,
        include_vectors=True,
    )

    executed_sql = mock_cursor.execute.call_args_list[0][0][0]
    assert 'WHERE "id" = (:bind_val1, :bind_val2, :bind_val3)' in executed_sql

    assert results is not None
    assert results.total_count == 1
    async for result in results.results:
        assert result.record.id == 1
        assert result.record.vector == [0.1, 0.2, 0.3]

    mock_cursor.fetchall.assert_awaited_once()
