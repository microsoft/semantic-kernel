# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import Annotated, Any
from unittest.mock import MagicMock, Mock, patch

from psycopg import Connection, Cursor
from psycopg_pool import ConnectionPool
from pytest import fixture, mark

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.memory.postgres.postgres_store import PostgresStore
from semantic_kernel.connectors.memory.postgres.utils import ConnectionPoolWrapper
from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@fixture(scope="function")
def mock_cursor():
    return MagicMock(spec=Cursor)


@fixture(autouse=True)
def mock_connection_pool(mock_cursor: Mock):
    with (
        patch(
            f"{ConnectionPoolWrapper.__module__}.{ConnectionPoolWrapper.__qualname__}.connection"
        ) as mock_pool_connection,
        patch(f"{ConnectionPoolWrapper.__module__}.{ConnectionPoolWrapper.__qualname__}.open") as mock_pool_open,
    ):
        mock_conn = MagicMock(spec=Connection)

        mock_pool_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_pool_open.return_value = None

        yield mock_pool_connection, mock_pool_open


@fixture
def vector_store(postgres_unit_test_env):
    return PostgresStore(env_file_path="test.env")


@vectorstoremodel
@dataclass
class SimpleDataModel:
    id: Annotated[int, VectorStoreRecordKeyField()]
    embedding: Annotated[
        list[float],
        VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
            index_kind="hnsw",
            dimensions=1536,
            distance_function="cosine",
            property_type="float",
        ),
    ]
    data: Annotated[
        dict[str, Any],
        VectorStoreRecordDataField(has_embedding=True, embedding_property_name="embedding", property_type="JSONB"),
    ]


def test_vector_store_defaults(vector_store: PostgresStore) -> None:
    assert vector_store.connection_pool is not None
    assert vector_store.connection_pool.open.call_count == 1
    with vector_store.connection_pool.connection() as conn:
        assert isinstance(conn, Mock)


def test_vector_store_with_connection_pool(vector_store: PostgresStore) -> None:
    connection_pool = MagicMock(spec=ConnectionPool)
    vector_store = PostgresStore(connection_pool=connection_pool)
    assert vector_store.connection_pool == connection_pool
    assert vector_store.connection_pool.open.call_count == 0


@mark.asyncio
async def test_list_collection_names(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    mock_cursor.fetchall.return_value = [
        ("test_collection",),
        ("test_collection_2",),
    ]
    names = await vector_store.list_collection_names()
    assert names == ["test_collection", "test_collection_2"]


def test_get_collection(vector_store: PostgresStore) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    assert collection.collection_name == "test_collection"


@mark.asyncio
async def test_does_collection_exist(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    mock_cursor.fetchall.return_value = [("test_collection",)]
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    result = await collection.does_collection_exist()
    assert result is True


@mark.asyncio
async def test_delete_collection(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.delete_collection()

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == 'DROP TABLE "public"."test_collection" CASCADE'


@mark.asyncio
async def test_delete_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.delete_batch([1, 2])

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == """DELETE FROM "public"."test_collection" WHERE "id" IN (1, 2)"""


@mark.asyncio
async def test_create_collection_simple_model(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.create_collection()

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == (
        'CREATE TABLE "public"."test_collection" ("id" INTEGER PRIMARY KEY, "embedding" VECTOR(1536), "data" JSONB)'
    )


@mark.asyncio
async def test_create_collection_model_with_python_types(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    @vectorstoremodel
    @dataclass
    class ModelWithImplicitTypes:
        name: Annotated[str, VectorStoreRecordKeyField()]
        age: Annotated[int, VectorStoreRecordDataField()]
        data: Annotated[dict[str, Any], VectorStoreRecordDataField(embedding_property_name="embedding")]
        embedding: Annotated[list[float], VectorStoreRecordVectorField(dimensions=20)]
        scores: Annotated[list[float], VectorStoreRecordDataField()]
        tags: Annotated[list[str], VectorStoreRecordDataField()]

    collection = vector_store.get_collection("test_collection", ModelWithImplicitTypes)

    await collection.create_collection()

    assert mock_cursor.execute.call_count == 1

    execute_args, _ = mock_cursor.execute.call_args

    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == (
        'CREATE TABLE "public"."test_collection" '
        '("name" TEXT PRIMARY KEY, "age" INTEGER, "data" JSONB, '
        '"embedding" VECTOR(20), "scores" DOUBLE PRECISION[], "tags" TEXT[])'
    )


@mark.asyncio
async def test_upsert_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.upsert_batch([
        SimpleDataModel(id=1, embedding=[1.0, 2.0, 3.0], data={"key": "value1"}),
        SimpleDataModel(id=2, embedding=[4.0, 5.0, 6.0], data={"key": "value2"}),
        SimpleDataModel(id=3, embedding=[5.0, 6.0, 1.0], data={"key": "value3"}),
    ])

    assert mock_cursor.executemany.call_count == 1
    execute_args, _ = mock_cursor.executemany.call_args
    statement_str = execute_args[0].as_string()
    values = execute_args[1]
    assert len(values) == 3

    assert statement_str == (
        'INSERT INTO "public"."test_collection" ("id", "embedding", "data") '
        "VALUES (%s, %s, %s) "
        'ON CONFLICT ("id") DO UPDATE SET "embedding" = EXCLUDED."embedding", "data" = EXCLUDED."data"'
    )

    assert values[0] == (1, [1.0, 2.0, 3.0], '{"key": "value1"}')
    assert values[1] == (2, [4.0, 5.0, 6.0], '{"key": "value2"}')
    assert values[2] == (3, [5.0, 6.0, 1.0], '{"key": "value3"}')


@mark.asyncio
async def test_get_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    mock_cursor.fetchall.return_value = [
        (1, "[1.0, 2.0, 3.0]", {"key": "value1"}),
        (2, "[4.0, 5.0, 6.0]", {"key": "value2"}),
        (3, "[5.0, 6.0, 1.0]", {"key": "value3"}),
    ]

    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    records = await collection.get_batch([1, 2, 3])

    assert len(records) == 3
    assert records[0].id == 1
    assert records[0].embedding == [1.0, 2.0, 3.0]
    assert records[0].data == {"key": "value1"}

    assert records[1].id == 2
    assert records[1].embedding == [4.0, 5.0, 6.0]
    assert records[1].data == {"key": "value2"}

    assert records[2].id == 3
    assert records[2].embedding == [5.0, 6.0, 1.0]
    assert records[2].data == {"key": "value3"}