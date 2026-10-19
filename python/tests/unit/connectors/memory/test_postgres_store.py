# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID

import pytest
import pytest_asyncio
from psycopg import AsyncConnection, AsyncCursor, ProgrammingError
from psycopg_pool import AsyncConnectionPool
from pytest import fixture

from semantic_kernel.connectors.postgres import (
    DISTANCE_COLUMN_NAME,
    PostgresCollection,
    PostgresSettings,
    PostgresStore,
)
from semantic_kernel.data._shared import default_dynamic_filter_function
from semantic_kernel.data.vector import (
    DistanceFunction,
    IndexKind,
    VectorSearchOptions,
    VectorStoreCollectionDefinition,
    VectorStoreField,
    vectorstoremodel,
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.functions import KernelParameterMetadata


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
    id: Annotated[int, VectorStoreField("key")]
    data: Annotated[
        list[float] | str | None,
        VectorStoreField(
            "vector",
            type="float",
            dimensions=1536,
            index_kind=IndexKind.HNSW,
            distance_function=DistanceFunction.COSINE_SIMILARITY,
        ),
    ] = None


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
    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    assert collection.collection_name == "test_collection"


async def test_collection_exists(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    mock_cursor.fetchall.return_value = [("test_collection",)]
    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    result = await collection.collection_exists()
    assert result is True


async def test_ensure_collection_deleted(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    await collection.ensure_collection_deleted()

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == 'DROP TABLE "public"."test_collection" CASCADE'


async def test_delete_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    await collection.delete([1, 2])

    assert mock_cursor.execute.call_count == 1
    execute_args, _ = mock_cursor.execute.call_args
    statement = execute_args[0]
    statement_str = statement.as_string()

    assert statement_str == """DELETE FROM "public"."test_collection" WHERE "id" IN (1, 2)"""


async def test_ensure_collection_exists_simple_model(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    await collection.ensure_collection_exists()

    # 2 calls, once for the table creation and once for the index creation
    assert mock_cursor.execute.call_count == 2

    # Check the table creation statement
    execute_args, _ = mock_cursor.execute.call_args_list[0]
    statement = execute_args[0]
    statement_str = statement.as_string()
    assert statement_str == ('CREATE TABLE "public"."test_collection" ("id" INTEGER PRIMARY KEY, "data" VECTOR(1536))')

    # Check the index creation statement
    execute_args, _ = mock_cursor.execute.call_args_list[1]
    statement = execute_args[0]
    statement_str = statement.as_string()
    assert statement_str == (
        'CREATE INDEX "test_collection_data_idx" ON "public"."test_collection" USING hnsw ("data" vector_cosine_ops)'
    )


async def test_ensure_collection_exists_model_with_python_types(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    @vectorstoremodel
    @dataclass
    class ModelWithImplicitTypes:
        name: Annotated[str, VectorStoreField("key")]
        age: Annotated[int, VectorStoreField("data")]
        data: Annotated[dict[str, Any], VectorStoreField("data")]
        embedding: Annotated[list[float], VectorStoreField("vector", dimensions=20)]
        scores: Annotated[list[float], VectorStoreField("data")]
        tags: Annotated[list[str], VectorStoreField("data")]

    collection = vector_store.get_collection(collection_name="test_collection", record_type=ModelWithImplicitTypes)

    await collection.ensure_collection_exists()

    assert mock_cursor.execute.call_count == 2

    # Check the table creation statement
    execute_args, _ = mock_cursor.execute.call_args_list[0]
    statement = execute_args[0]
    statement_str = statement.as_string()
    assert statement_str == (
        'CREATE TABLE "public"."test_collection" '
        '("name" TEXT PRIMARY KEY, "age" INTEGER, "data" JSONB, '
        '"embedding" VECTOR(20), "scores" DOUBLE PRECISION[], "tags" TEXT[])'
    )

    # Check the index creation statement
    execute_args, _ = mock_cursor.execute.call_args_list[1]
    statement = execute_args[0]
    statement_str = statement.as_string()
    assert statement_str == (
        'CREATE INDEX "test_collection_embedding_idx" ON "public"."test_collection" '
        'USING hnsw ("embedding" vector_cosine_ops)'
    )


async def test_ensure_collection_exists_model_with_common_postgres_types(
    vector_store: PostgresStore, mock_cursor: Mock
) -> None:
    @vectorstoremodel
    @dataclass
    class ModelWithCommonPostgresTypes:
        name: Annotated[str, VectorStoreField("key")]
        event_date: Annotated[date, VectorStoreField("data")]
        external_id: Annotated[UUID, VectorStoreField("data")]
        amount: Annotated[Decimal, VectorStoreField("data")]

    collection = vector_store.get_collection(
        collection_name="test_collection",
        record_type=ModelWithCommonPostgresTypes,
    )

    await collection.ensure_collection_exists()

    mock_cursor.execute.assert_awaited_once()
    statement = mock_cursor.execute.call_args.args[0]
    assert statement.as_string() == (
        'CREATE TABLE "public"."test_collection" '
        '("name" TEXT PRIMARY KEY, "event_date" DATE, "external_id" UUID, "amount" DECIMAL)'
    )


async def test_ensure_collection_exists_explicit_definition_with_supported_aliases(
    vector_store: PostgresStore, mock_cursor: Mock
) -> None:
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="int"),
            VectorStoreField("data", name="title", type="text"),
            VectorStoreField("data", name="count", type="INTEGER"),
            VectorStoreField("data", name="large_count", type="bigint"),
            VectorStoreField("data", name="small_count", type="SMALLINT"),
            VectorStoreField("data", name="score", type="double precision"),
            VectorStoreField("data", name="approximate_score", type="real"),
            VectorStoreField("data", name="enabled", type="BOOLEAN"),
            VectorStoreField("data", name="metadata", type="jsonb"),
            VectorStoreField("data", name="created_at", type="TIMESTAMP"),
            VectorStoreField("data", name="processed_at", type="timestamptz"),
            VectorStoreField("data", name="payload", type="bytea"),
            VectorStoreField("data", name="summary", type="varchar(255)"),
            VectorStoreField("data", name="description", type="character varying ( 1024 )"),
            VectorStoreField("data", name="amount", type="numeric(10, 2)"),
            VectorStoreField("data", name="ratio", type="decimal(6)"),
            VectorStoreField("data", name="tags", type="list[str]"),
            VectorStoreField("data", name="codes", type="varchar(12)[]"),
            VectorStoreField("data", name="weights", type="DOUBLE PRECISION[]"),
            VectorStoreField("data", name="items", type="Dict[str, Any]"),
            VectorStoreField("data", name="item_history", type="Dict[str, Any][]"),
            VectorStoreField("data", name="nested_item_history", type="dict[str, list[int]][][]"),
        ]
    )
    collection = vector_store.get_collection(
        collection_name="test_collection",
        record_type=dict,
        definition=definition,
    )

    await collection.ensure_collection_exists()

    mock_cursor.execute.assert_awaited_once()
    statement = mock_cursor.execute.call_args.args[0]
    assert statement.as_string() == (
        'CREATE TABLE "public"."test_collection" '
        '("id" INTEGER PRIMARY KEY, "title" TEXT, "count" INTEGER, "large_count" BIGINT, '
        '"small_count" SMALLINT, "score" DOUBLE PRECISION, "approximate_score" REAL, "enabled" BOOLEAN, '
        '"metadata" JSONB, "created_at" TIMESTAMP, "processed_at" TIMESTAMP WITH TIME ZONE, "payload" BYTEA, '
        '"summary" VARCHAR(255), "description" CHARACTER VARYING(1024), "amount" NUMERIC(10, 2), '
        '"ratio" DECIMAL(6), "tags" TEXT[], "codes" VARCHAR(12)[], "weights" DOUBLE PRECISION[], '
        '"items" JSONB, "item_history" JSONB[], "nested_item_history" JSONB[][])'
    )


@pytest.mark.parametrize(
    "unsupported_type",
    [
        "TEXT); SELECT 1; --",
        "TEXT -- comment",
        "TEXT/*comment*/",
        "TEXT\n); SELECT 1",
        "list[int",
        "list[]",
        "INTEGER[",
        "INTEGER[] trailing",
        "list[custom_type]",
        "Dict[str, Any]]",
        "list[Dict[str, Any]]]",
        "dict[str, Any -- comment]",
        "varchar()",
        "varchar(255, 1)",
        "varchar(255); SELECT 1",
        "varchar(123456789)",
        "numeric()",
        "numeric(10, 2, 1)",
        "numeric(10, scale)",
        "numeric(12345)",
    ],
)
async def test_ensure_collection_exists_rejects_unsupported_types_before_execution(
    vector_store: PostgresStore,
    mock_cursor: Mock,
    mock_connection_pool,
    unsupported_type: str,
) -> None:
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="int"),
            VectorStoreField("data", name="content", type=unsupported_type),
        ]
    )
    collection = vector_store.get_collection(
        collection_name="test_collection",
        record_type=dict,
        definition=definition,
    )

    with pytest.raises(VectorStoreModelValidationError, match="not supported for automatic collection creation"):
        await collection.ensure_collection_exists()

    mock_cursor.execute.assert_not_awaited()
    mock_connection_pool[0].assert_not_called()


async def test_upsert_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    await collection.upsert([
        SimpleDataModel(id=1, data=[1.0, 2.0, 3.0]),
        SimpleDataModel(id=2, data=[4.0, 5.0, 6.0]),
        SimpleDataModel(id=3, data=[5.0, 6.0, 1.0]),
    ])

    assert mock_cursor.executemany.call_count == 1
    execute_args, _ = mock_cursor.executemany.call_args
    statement_str = execute_args[0].as_string()
    values = execute_args[1]
    assert len(values) == 3

    assert statement_str == (
        'INSERT INTO "public"."test_collection" ("id", "data") '
        "VALUES (%s, %s) "
        'ON CONFLICT ("id") DO UPDATE SET "data" = EXCLUDED."data"'
    )

    assert values[0] == (1, [1.0, 2.0, 3.0])
    assert values[1] == (2, [4.0, 5.0, 6.0])
    assert values[2] == (3, [5.0, 6.0, 1.0])


async def test_get_records(vector_store: PostgresStore, mock_cursor: Mock) -> None:
    mock_cursor.fetchall.return_value = [
        (1, "[1.0, 2.0, 3.0]", {"key": "value1"}),
        (2, "[4.0, 5.0, 6.0]", {"key": "value2"}),
        (3, "[5.0, 6.0, 1.0]", {"key": "value3"}),
    ]

    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    records = await collection.get([1, 2, 3])

    assert len(records) == 3
    assert records[0].id == 1
    assert records[1].id == 2
    assert records[2].id == 3


# endregion

# region Vector Search tests


@pytest.mark.parametrize(
    "filter, filter_sql, filter_params",
    [
        (None, "", []),
        ("lambda x: x.id == 1", ' WHERE ("id" = %s)', [1]),
        (
            ["lambda x: x.id > 0", "lambda x: x.id == 1 or x.id == 2"],
            ' WHERE ("id" > %s) AND (("id" = %s OR "id" = %s))',
            [0, 1, 2],
        ),
    ],
)
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
    filter: str | list[str] | None,
    filter_sql: str,
    filter_params: list[Any],
) -> None:
    @vectorstoremodel
    @dataclass
    class SimpleDataModel:
        id: Annotated[int, VectorStoreField("key")]
        embedding: Annotated[
            list[float] | str | None,
            VectorStoreField(
                "vector",
                index_kind=IndexKind.HNSW,
                dimensions=1536,
                distance_function=distance_function,
                type="float",
            ),
        ]
        data: Annotated[
            dict[str, Any],
            VectorStoreField("data", type="JSONB"),
        ]

        def model_post_init(self, context: Any) -> None:
            if self.embedding is None:
                self.embedding = self.data

    collection = vector_store.get_collection(collection_name="test_collection", record_type=SimpleDataModel)
    assert isinstance(collection, PostgresCollection)

    search_results = await collection.search(
        vector=[1.0, 2.0, 3.0],
        top=10,
        skip=5,
        include_vectors=include_vectors,
        include_total_count=include_total_count,
        filter=filter,
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
        f'FROM "public"."test_collection"{filter_sql} '
        f'ORDER BY "{DISTANCE_COLUMN_NAME}" LIMIT 10 OFFSET 5'
    )

    if subquery_distance:
        expected_statement = (
            f'SELECT subquery.*, {subquery_distance} AS "{DISTANCE_COLUMN_NAME}" FROM ('
            + expected_statement
            + ") AS subquery"
        )

    assert statement_str == expected_statement
    assert execute_args[1] == ["[1.0,2.0,3.0]", *filter_params]


@fixture
def filter_collection(vector_store):
    @vectorstoremodel
    @dataclass
    class FilterRecord:
        id: Annotated[int, VectorStoreField("key")]
        tenant: Annotated[str, VectorStoreField("data")]
        embedding: Annotated[
            list[float],
            VectorStoreField("vector", dimensions=3, distance_function=DistanceFunction.COSINE_DISTANCE),
        ]
        label: Annotated[str, VectorStoreField("data", storage_name='label"name')] = ""

    return vector_store.get_collection(collection_name="filter_records", record_type=FilterRecord)


@pytest.mark.parametrize(
    "expression, expected_sql, expected_params",
    [
        ("x.id == 1", '"id" = %s', [1]),
        ("x.id != 1", '"id" <> %s', [1]),
        ("x.id > 1", '"id" > %s', [1]),
        ("x.id >= 1", '"id" >= %s', [1]),
        ("x.id < 1", '"id" < %s', [1]),
        ("x.id <= 1", '"id" <= %s', [1]),
        ("x.id in [1, 2]", '"id" IN (%s, %s)', [1, 2]),
        ("x.id not in [1, 2]", '"id" NOT IN (%s, %s)', [1, 2]),
        ("x.id == 1 and x.id < 3", '("id" = %s AND "id" < %s)', [1, 3]),
        ("x.id == 1 or x.id == 2", '("id" = %s OR "id" = %s)', [1, 2]),
        ("not x.id == 1", 'NOT ("id" = %s)', [1]),
        ("0 < x.id < 3", '(%s < "id" AND "id" < %s)', [0, 3]),
        ("x.id < 2 < 3", '("id" < %s AND %s < %s)', [2, 2, 3]),
        ("x.id == 1.5", '"id" = %s', [1.5]),
        ("x.id == True", '"id" = %s', [True]),
        ("x.id == False", '"id" = %s', [False]),
        ("x.id == x.id", '"id" = "id"', []),
        ("id == 1", '"id" = %s', [1]),
        (
            "(x.id == 1 or x.id == 2) and not x.tenant == 'other'",
            '(("id" = %s OR "id" = %s) AND NOT ("tenant" = %s))',
            [1, 2, "other"],
        ),
    ],
)
def test_filter_parser(filter_collection, expression, expected_sql, expected_params):
    clause, params = filter_collection._build_filter(f"lambda x: {expression}")

    assert clause.as_string() == expected_sql
    assert params == expected_params
    assert [type(value) for value in params] == [type(value) for value in expected_params]


@pytest.mark.parametrize(
    "expression, expected_sql, expected_params",
    [
        ("x.tenant == None", '"tenant" IS NULL', []),
        ("x.tenant != None", '"tenant" IS NOT NULL', []),
        ("None == x.tenant", '"tenant" IS NULL', []),
        ("None != x.tenant", '"tenant" IS NOT NULL', []),
        ("None == None", "TRUE", []),
        ("None != None", "FALSE", []),
        ("'value' != None", "TRUE", []),
        ("None == 'value'", "FALSE", []),
        ("0 != None", "TRUE", []),
        ("False == None", "FALSE", []),
        ("not x.tenant == None", 'NOT ("tenant" IS NULL)', []),
        ("not x.tenant != None", 'NOT ("tenant" IS NOT NULL)', []),
        ("x.tenant == None or x.id == 1", '("tenant" IS NULL OR "id" = %s)', [1]),
        ("None == x.tenant == None", '("tenant" IS NULL AND "tenant" IS NULL)', []),
        ("'value' == x.tenant != None", '(%s = "tenant" AND "tenant" IS NOT NULL)', ["value"]),
    ],
)
def test_null_filter_parser(filter_collection, expression, expected_sql, expected_params):
    clause, params = filter_collection._build_filter(f"lambda x: {expression}")

    assert clause.as_string() == expected_sql
    assert params == expected_params


def test_null_filter_query_parameter_order(filter_collection):
    filters = [
        "lambda x: x.id > 0",
        "lambda x: x.tenant == None or x.tenant == 'value'",
        "lambda x: x.id < 5",
    ]
    query, params, _ = filter_collection._construct_vector_query([1, 0, 0], VectorSearchOptions(filter=filters))

    assert query.as_string() == (
        'SELECT "id", "tenant", "label""name", "embedding" <=> %s as "sk_pg_distance" '
        'FROM "public"."filter_records" WHERE ("id" > %s) '
        'AND (("tenant" IS NULL OR "tenant" = %s)) AND ("id" < %s) ORDER BY "sk_pg_distance" LIMIT 3'
    )
    assert params == ["[1.0,0.0,0.0]", 0, "value", 5]


def test_dynamic_null_filter(filter_collection):
    filter = default_dynamic_filter_function(parameters=[KernelParameterMetadata(name="tenant")], tenant=None)
    clause, params = filter_collection._build_filter(filter)

    assert clause.as_string() == '"tenant" IS NULL'
    assert params == []


@pytest.mark.parametrize(
    "value",
    ["tenant_a", "", "O'Brien", "\\", "a\\' OR 1=1 --", "'; SELECT 1; --", "50%_%s\nnext", "\u00e9"],
)
def test_filter_values_are_parameters(filter_collection, value):
    filter = default_dynamic_filter_function(
        parameters=[KernelParameterMetadata(name="tenant")],
        tenant=value,
    )
    query, params, _ = filter_collection._construct_vector_query(
        [1, 0, 0], VectorSearchOptions(filter=filter, include_total_count=True)
    )

    assert query.as_string() == (
        'SELECT "id", "tenant", "label""name", "embedding" <=> %s as "sk_pg_distance" '
        'FROM "public"."filter_records" WHERE ("tenant" = %s) ORDER BY "sk_pg_distance" LIMIT 3'
    )
    assert params == ["[1.0,0.0,0.0]", value]


def test_callable_filter(filter_collection):
    clause, params = filter_collection._build_filter(lambda x: x.tenant == "tenant_a")

    assert clause.as_string() == '"tenant" = %s'
    assert params == ["tenant_a"]


def test_filter_identifier_quoting(filter_collection):
    clause, params = filter_collection._lambda_parser(ast.Name(id='label"name'))

    assert clause.as_string() == '"label""name"'
    assert params == []


@pytest.mark.parametrize(
    "expression, error",
    [
        ("x.unknown == 1", VectorStoreOperationException),
        ("x.unknown == None", VectorStoreOperationException),
        ("None != x.unknown", VectorStoreOperationException),
        ("unknown == 1", VectorStoreOperationException),
        ("x.id in []", VectorStoreOperationException),
        ("x.id not in []", VectorStoreOperationException),
        ("x.id == b'bytes'", VectorStoreOperationException),
        ("x.id == 1j", VectorStoreOperationException),
        ("None == b'bytes'", VectorStoreOperationException),
        ("1j != None", VectorStoreOperationException),
        ("x.id is None", NotImplementedError),
        ("x.id is not None", NotImplementedError),
        ("x.id == -1", NotImplementedError),
        ("x.id == +1", NotImplementedError),
        ("x.id == ~1", NotImplementedError),
        ("x.tenant.startswith('a')", NotImplementedError),
        ("x.id in (1, 2)", NotImplementedError),
    ],
)
def test_filter_rejects_unsupported_input(filter_collection, expression, error):
    with pytest.raises(error):
        filter_collection._construct_vector_query([1, 0, 0], VectorSearchOptions(filter=f"lambda x: {expression}"))


def test_filter_rejects_raw_sql(filter_collection):
    with pytest.raises((SyntaxError, VectorStoreOperationException)):
        filter_collection._build_filter("tenant = 'tenant_a'")


@pytest.mark.parametrize("include_total_count", [False, True])
async def test_filtered_search_error_is_not_retried(filter_collection, mock_cursor, include_total_count):
    mock_cursor.execute.side_effect = ProgrammingError("test query failure")

    with pytest.raises((ProgrammingError, VectorSearchExecutionException)):
        results = await filter_collection.search(
            vector=[1, 0, 0], filter="lambda x: x.tenant == 'tenant_a'", include_total_count=include_total_count
        )
        async for _ in results.results:
            pass

    assert mock_cursor.execute.call_count == 1
    assert ' WHERE ("tenant" = %s)' in mock_cursor.execute.call_args.args[0].as_string()
    assert mock_cursor.execute.call_args.args[1] == ["[1.0,0.0,0.0]", "tenant_a"]


async def test_concurrent_filtered_searches_keep_separate_parameters(filter_collection, mock_cursor):
    async def search(tenant):
        results = await filter_collection.search(vector=[1, 0, 0], filter=f"lambda x: x.tenant == {tenant!r}")
        await asyncio.sleep(0)
        return [result async for result in results.results]

    await asyncio.gather(search("tenant_a"), search("tenant_b"))

    assert [call.args[1] for call in mock_cursor.execute.call_args_list] == [
        ["[1.0,0.0,0.0]", "tenant_a"],
        ["[1.0,0.0,0.0]", "tenant_b"],
    ]


async def test_model_post_init_conflicting_distance_column_name(vector_store: PostgresStore) -> None:
    @vectorstoremodel
    @dataclass
    class ConflictingDataModel:
        id: Annotated[int, VectorStoreField("key")]
        sk_pg_distance: Annotated[
            float, VectorStoreField("data")
        ]  # Note: test depends on value of DISTANCE_COLUMN_NAME constant

        embedding: Annotated[
            list[float],
            VectorStoreField(
                "vector",
                index_kind=IndexKind.HNSW,
                dimensions=1536,
                distance_function=DistanceFunction.COSINE_SIMILARITY,
                type="float",
            ),
        ]
        data: Annotated[
            dict[str, Any],
            VectorStoreField("data", type="JSONB"),
        ]

    collection = vector_store.get_collection(collection_name="test_collection", record_type=ConflictingDataModel)
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
