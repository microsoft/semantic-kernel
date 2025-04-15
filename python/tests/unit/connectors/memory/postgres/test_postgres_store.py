# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio
from psycopg import AsyncConnection, AsyncCursor
from psycopg_pool import AsyncConnectionPool
from pytest import fixture

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.memory.postgres.constants import DISTANCE_COLUMN_NAME
from semantic_kernel.connectors.memory.postgres.postgres_collection import PostgresCollection
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings
from semantic_kernel.connectors.memory.postgres.postgres_store import PostgresStore
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)
from semantic_kernel.data.vector_search import VectorSearchOptions


@fixture(scope="function")
def mock_cursor():
    return AsyncMock(spec=AsyncCursor)


@fixture(autouse=True)
def mock_connection_pool(mock_cursor: Mock):
    with (
        patch(
            f"{AsyncConnectionPool.__module__}.{AsyncConnectionPool.__qualname__}.connection",
        ) as mock_pool_connection,
        patch(
            f"{AsyncConnectionPool.__module__}.{AsyncConnectionPool.__qualname__}.open",
            new_callable=AsyncMock,
        ) as mock_pool_open,
    ):
        mock_conn = AsyncMock(spec=AsyncConnection)

        mock_pool_connection.return_value.__aenter__.return_value = mock_conn
        mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

        mock_pool_open.return_value = None

        yield mock_pool_connection, mock_pool_open


@pytest_asyncio.fixture
async def vector_store(postgres_unit_test_env) -> AsyncGenerator[PostgresStore, None]:
    async with await PostgresSettings(env_file_path="test.env").create_connection_pool() as pool:
        yield PostgresStore(connection_pool=pool)


@vectorstoremodel
@dataclass
class SimpleDataModel:
    id: Annotated[int, VectorStoreRecordKeyField()]
    embedding: Annotated[
        list[float],
        VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
            index_kind=IndexKind.HNSW,
            dimensions=1536,
            distance_function=DistanceFunction.COSINE_SIMILARITY,
            property_type="float",
        ),
    ]
    data: Annotated[
        dict[str, Any],
        VectorStoreRecordDataField(has_embedding=True, embedding_property_name="embedding", property_type="JSONB"),
    ]


# region VectorStore Tests


async def test_vector_store_defaults(vector_store: PostgresStore) -> None:
    assert vector_store.connection_pool is not None
    async with vector_store.connection_pool.connection() as conn:
        assert isinstance(conn, Mock)


def test_vector_store_with_connection_pool(vector_store: PostgresStore) -> None:
    connection_pool = MagicMock(spec=AsyncConnectionPool)
    vector_store = PostgresStore(connection_pool=connection_pool)
    assert vector_store.connection_pool == connection_pool


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


async def test_does_collection_exist(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    mock_cursor.fetchall.return_value = [("test_collection",)]
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    result = await collection.does_collection_exist()
    assert result is True


async def test_delete_collection(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.delete_collection()

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == 'DROP TABLE "public"."test_collection" CASCADE'


async def test_delete_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.delete_batch([1, 2])

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == """DELETE FROM "public"."test_collection" WHERE "id" IN (1, 2)"""


async def test_create_collection_simple_model(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    await collection.create_collection()

    # 2 calls, once for the table creation and once for the index creation
    assert mock_cursor.execute.call_count == 2

    # Check the table creation statement
    execute_args, _ = mock_cursor.execute.call_args_list[0]
    statement = execute_args[0]
    statement_str = statement.as_string()
    assert statement_str == (
        'CREATE TABLE "public"."test_collection" ("id" INTEGER PRIMARY KEY, "embedding" VECTOR(1536), "data" JSONB)'
    )

    # Check the index creation statement
    execute_args, _ = mock_cursor.execute.call_args_list[1]
    statement = execute_args[0]
    statement_str = statement.as_string()
    assert statement_str == (
        'CREATE INDEX "test_collection_embedding_idx" ON "public"."test_collection" '
        'USING hnsw ("embedding" vector_cosine_ops)'
    )


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


# endregion

# region Vector Search tests


@pytest.mark.parametrize(
    "distance_function, operator, subquery_distance, include_vectors, include_total_count",
    [
        (DistanceFunction.COSINE_SIMILARITY, "<=>", f'1 - subquery."{DISTANCE_COLUMN_NAME}"', False, False),
        (DistanceFunction.COSINE_DISTANCE, "<=>", None, False, False),
        (DistanceFunction.DOT_PROD, "<#>", f'-1 * subquery."{DISTANCE_COLUMN_NAME}"', True, False),
        (DistanceFunction.EUCLIDEAN_DISTANCE, "<->", None, False, True),
        (DistanceFunction.MANHATTAN, "<+>", None, True, True),
    ],
)
async def test_vector_search(
    vector_store: PostgresStore,
    mock_cursor: Mock,
    distance_function: DistanceFunction,
    operator: str,
    subquery_distance: str | None,
    include_vectors: bool,
    include_total_count: bool,
) -> None:
    @vectorstoremodel
    @dataclass
    class SimpleDataModel:
        id: Annotated[int, VectorStoreRecordKeyField()]
        embedding: Annotated[
            list[float],
            VectorStoreRecordVectorField(
                embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=IndexKind.HNSW,
                dimensions=1536,
                distance_function=distance_function,
                property_type="float",
            ),
        ]
        data: Annotated[
            dict[str, Any],
            VectorStoreRecordDataField(has_embedding=True, embedding_property_name="embedding", property_type="JSONB"),
        ]

    collection = vector_store.get_collection("test_collection", SimpleDataModel)
    assert isinstance(collection, PostgresCollection)

    search_results = await collection.vectorized_search(
        [1.0, 2.0, 3.0],
        options=VectorSearchOptions(
            top=10, skip=5, include_vectors=include_vectors, include_total_count=include_total_count
        ),
    )
    if include_total_count:
        # Including total count issues query directly
        assert mock_cursor.execute.call_count == 1
    else:
        # Total count is not included, query is issued when iterating over results
        assert mock_cursor.execute.call_count == 0
        async for _ in search_results.results:
            pass
        assert mock_cursor.execute.call_count == 1

    execute_args, _ = mock_cursor.execute.call_args

    assert (search_results.total_count is not None) == include_total_count

    statement = execute_args[0]
    statement_str = statement.as_string()

    expected_columns = '"id", "data"'
    if include_vectors:
        expected_columns = '"id", "embedding", "data"'

    expected_statement = (
        f'SELECT {expected_columns}, "embedding" {operator} %s as "{DISTANCE_COLUMN_NAME}" '
        'FROM "public"."test_collection" '
        f'ORDER BY "{DISTANCE_COLUMN_NAME}" LIMIT 10 OFFSET 5'
    )

    if subquery_distance:
        expected_statement = (
            f'SELECT subquery.*, {subquery_distance} AS "{DISTANCE_COLUMN_NAME}" FROM ('
            + expected_statement
            + ") AS subquery"
        )

    assert statement_str == expected_statement


async def test_model_post_init_conflicting_distance_column_name(vector_store: PostgresStore) -> None:
    @vectorstoremodel
    @dataclass
    class ConflictingDataModel:
        id: Annotated[int, VectorStoreRecordKeyField()]
        sk_pg_distance: Annotated[
            float, VectorStoreRecordDataField()
        ]  # Note: test depends on value of DISTANCE_COLUMN_NAME constant

        embedding: Annotated[
            list[float],
            VectorStoreRecordVectorField(
                embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=IndexKind.HNSW,
                dimensions=1536,
                distance_function=DistanceFunction.COSINE_SIMILARITY,
                property_type="float",
            ),
        ]
        data: Annotated[
            dict[str, Any],
            VectorStoreRecordDataField(has_embedding=True, embedding_property_name="embedding", property_type="JSONB"),
        ]

    collection = vector_store.get_collection("test_collection", ConflictingDataModel)
    assert isinstance(collection, PostgresCollection)

    # Ensure that the distance column name has been changed to avoid conflict
    assert collection._distance_column_name != DISTANCE_COLUMN_NAME
    assert collection._distance_column_name.startswith(f"{DISTANCE_COLUMN_NAME}_")


# endregion

# region Settings tests


def test_settings_connection_string(monkeypatch) -> None:
    monkeypatch.delenv("PGHOST", raising=False)
    monkeypatch.delenv("PGPORT", raising=False)
    monkeypatch.delenv("PGDATABASE", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    monkeypatch.delenv("PGPASSWORD", raising=False)

    settings = PostgresSettings(connection_string="host=localhost port=5432 dbname=dbname user=user password=password")
    conn_info = settings.get_connection_args()

    assert conn_info["host"] == "localhost"
    assert conn_info["port"] == 5432
    assert conn_info["dbname"] == "dbname"
    assert conn_info["user"] == "user"
    assert conn_info["password"] == "password"


def test_settings_env_connection_string(monkeypatch) -> None:
    monkeypatch.delenv("PGHOST", raising=False)
    monkeypatch.delenv("PGPORT", raising=False)
    monkeypatch.delenv("PGDATABASE", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)
    monkeypatch.delenv("PGPASSWORD", raising=False)

    monkeypatch.setenv(
        "POSTGRES_CONNECTION_STRING", "host=localhost port=5432 dbname=dbname user=user password=password"
    )

    settings = PostgresSettings()
    conn_info = settings.get_connection_args()
    assert conn_info["host"] == "localhost"
    assert conn_info["port"] == 5432
    assert conn_info["dbname"] == "dbname"
    assert conn_info["user"] == "user"
    assert conn_info["password"] == "password"


def test_settings_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")
    monkeypatch.setenv("PGDATABASE", "dbname")
    monkeypatch.setenv("PGUSER", "user")
    monkeypatch.setenv("PGPASSWORD", "password")

    settings = PostgresSettings()
    conn_info = settings.get_connection_args()
    assert conn_info["host"] == "localhost"
    assert conn_info["port"] == 5432
    assert conn_info["dbname"] == "dbname"
    assert conn_info["user"] == "user"
    assert conn_info["password"] == "password"


# endregion
