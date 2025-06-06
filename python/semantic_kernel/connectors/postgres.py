# Copyright (c) Microsoft. All rights reserved.

import ast
import json
import logging
import random
import re
import string
import sys
from collections.abc import AsyncGenerator, MutableSequence, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, TypeVar

from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg_pool import AsyncConnectionPool
from pydantic import Field, PrivateAttr, SecretStr
from pydantic_settings import SettingsConfigDict

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DistanceFunction,
    FieldTypes,
    GetFilteredRecordOptions,
    IndexKind,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    VectorStoreField,
)
from semantic_kernel.exceptions import VectorStoreModelValidationError, VectorStoreOperationException
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorConnectionException
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if TYPE_CHECKING:
    from psycopg_pool.abc import ACT

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


logger = logging.getLogger(__name__)
TKey = TypeVar("TKey", bound=str | int)
# region: Constants

DEFAULT_SCHEMA: Final[str] = "public"
# Limitation based on pgvector documentation https://github.com/pgvector/pgvector#what-if-i-want-to-index-vectors-with-more-than-2000-dimensions
MAX_DIMENSIONALITY: Final[int] = 2000
# The name of the column that returns distance value in the database.
# It is used in the similarity search query. Must not conflict with model property.
DISTANCE_COLUMN_NAME: Final[str] = "sk_pg_distance"
# Environment Variables
PGHOST_ENV_VAR: Final[str] = "PGHOST"
PGPORT_ENV_VAR: Final[str] = "PGPORT"
PGDATABASE_ENV_VAR: Final[str] = "PGDATABASE"
PGUSER_ENV_VAR: Final[str] = "PGUSER"
PGPASSWORD_ENV_VAR: Final[str] = "PGPASSWORD"
PGSSL_MODE_ENV_VAR: Final[str] = "PGSSL_MODE"


DISTANCE_FUNCTION_MAP_STRING: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_DISTANCE: "vector_cosine_ops",
    DistanceFunction.COSINE_SIMILARITY: "vector_cosine_ops",
    DistanceFunction.DOT_PROD: "vector_ip_ops",
    DistanceFunction.EUCLIDEAN_DISTANCE: "vector_l2_ops",
    DistanceFunction.MANHATTAN: "vector_l1_ops",
    DistanceFunction.HAMMING: "bit_hamming_ops",
    DistanceFunction.DEFAULT: "vector_cosine_ops",
}

DISTANCE_FUNCTION_MAP_OPS: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_DISTANCE: "<=>",
    DistanceFunction.COSINE_SIMILARITY: "<=>",
    DistanceFunction.DOT_PROD: "<#>",
    DistanceFunction.EUCLIDEAN_DISTANCE: "<->",
    DistanceFunction.MANHATTAN: "<+>",
    DistanceFunction.DEFAULT: "<=>",
}
INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {
    IndexKind.HNSW: "hnsw",
    IndexKind.IVF_FLAT: "ivfflat",
    IndexKind.DEFAULT: "hnsw",
}

# region: Helpers


def _python_type_to_postgres(python_type_str: str) -> str | None:
    """Convert a string representation of a Python type to a PostgreSQL data type.

    Args:
        python_type_str: The string representation of the Python type (e.g., "int", "List[str]").

    Returns:
        Corresponding PostgreSQL data type as a string, if found. If the type is not found, return None.
    """
    # Basic type mapping from Python types (in string form) to PostgreSQL types
    type_mapping = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "DOUBLE PRECISION",
        "bool": "BOOLEAN",
        "dict": "JSONB",
        "datetime": "TIMESTAMP",
        "bytes": "BYTEA",
        "NoneType": "NULL",
    }

    # Regular expression to detect lists, e.g., "List[str]" or "List[int]"
    list_pattern = re.compile(r"(?i)List\[(.*)\]")

    # Check if the type is a list
    match = list_pattern.match(python_type_str)
    if match:
        # Extract the inner type of the list and convert it to a PostgreSQL array type
        element_type_str = match.group(1)
        postgres_element_type = _python_type_to_postgres(element_type_str)
        return f"{postgres_element_type}[]"

    # Check if the type is a dictionary
    dict_pattern = re.compile(r"(?i)Dict\[(.*), (.*)\]")
    match = dict_pattern.match(python_type_str)
    if match:
        return "JSONB"

    # Handle basic types
    if python_type_str in type_mapping:
        return type_mapping[python_type_str]

    return None


def _convert_row_to_dict(row: tuple[Any, ...], fields: Sequence[tuple[str, VectorStoreField | None]]) -> dict[str, Any]:
    """Convert a row from a PostgreSQL query to a dictionary.

    Uses the field information to map the row values to the corresponding field names.

    Args:
        row: A row from a PostgreSQL query, represented as a tuple.
        fields: A list of tuples, where each tuple contains the field name and field definition.

    Returns:
        A dictionary representation of the row.
    """

    def _convert(v: Any | None, field: VectorStoreField | None) -> Any | None:
        if v is None:
            return None
        if field and field.field_type == FieldTypes.VECTOR and isinstance(v, str):
            # psycopg returns vector as a string if pgvector is not loaded.
            # If pgvector is registered with the connection, no conversion is required.
            return json.loads(v)
        return v

    return {field_name: _convert(value, field) for (field_name, field), value in zip(fields, row)}


def _convert_dict_to_row(
    record: dict[str, Any],
    fields: list[VectorStoreField],
) -> tuple[Any, ...]:
    """Convert a dictionary to a row for a PostgreSQL query.

    Args:
        record: A dictionary representing a record.
        fields: A list of tuples, where each tuple contains the field name and field definition.

    Returns:
        A tuple representing the record.
    """

    def _convert(v: Any | None) -> Any | None:
        if isinstance(v, dict):
            # psycopg requires serializing dicts as strings.
            return json.dumps(v)
        return v

    return tuple(_convert(record.get(field.storage_name or field.name)) for field in fields)


# region: Settings


@release_candidate
class PostgresSettings(KernelBaseSettings):
    """Postgres model settings.

    This class is used to configure the Postgres connection pool
    and other settings related to the Postgres store.

    The settings that match what can be configured on tools such as
    psql, pg_dump, pg_restore, pgbench, createdb, and
    `libpq <https://www.postgresql.org/docs/current/libpq-envars.html>`_
    match the environment variables used by those tools. This includes
    PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, and PGSSL_MODE.
    Other settings follow the standard pattern of Pydantic settings,
    e.g. POSTGRES_CONNECTION_STRING.

    Args:
        connection_string: Postgres connection string
        (Env var POSTGRES_CONNECTION_STRING)
        host: Postgres host (Env var PGHOST or POSTGRES_HOST)
        port: Postgres port (Env var PGPORT or POSTGRES_PORT)
        dbname: Postgres database name (Env var PGDATABASE or POSTGRES_DBNAME)
        user: Postgres user (Env var PGUSER or POSTGRES_USER)
        password: Postgres password (Env var PGPASSWORD or POSTGRES_PASSWORD)
        sslmode: Postgres sslmode (Env var PGSSL_MODE or POSTGRES_SSL_MODE)
            Use "require" to require SSL, "disable" to disable SSL, or "prefer" to prefer
            SSL but allow a connection without it. Defaults to "prefer".
        min_pool: Minimum connection pool size. Defaults to 1.
            (Env var POSTGRES_MIN_POOL)
        max_pool: Maximum connection pool size. Defaults to 5.
            (Env var POSTGRES_MAX_POOL)
        default_dimensionality: Default dimensionality for vectors. Defaults to 100.
            (Env var POSTGRES_DEFAULT_DIMENSIONALITY)
        max_rows_per_transaction: Maximum number of rows to process in a single transaction. Defaults to 1000.
            (Env var POSTGRES_MAX_ROWS_PER_TRANSACTION)
    """

    env_prefix: ClassVar[str] = "POSTGRES_"

    connection_string: SecretStr | None = None
    host: str | None = Field(default=None, validation_alias=PGHOST_ENV_VAR)
    port: int | None = Field(default=5432, validation_alias=PGPORT_ENV_VAR)
    dbname: str | None = Field(default=None, validation_alias=PGDATABASE_ENV_VAR)
    user: str | None = Field(default=None, validation_alias=PGUSER_ENV_VAR)
    password: SecretStr | None = Field(default=None, validation_alias=PGPASSWORD_ENV_VAR)
    sslmode: str | None = Field(default=None, validation_alias=PGSSL_MODE_ENV_VAR)

    min_pool: int = 1
    max_pool: int = 5

    default_dimensionality: int = 100
    max_rows_per_transaction: int = 1000

    model_config = SettingsConfigDict(
        validate_by_name=True,
        validate_by_alias=True,
        extra="ignore",
        case_sensitive=False,
    )

    def get_connection_args(self) -> dict[str, Any]:
        """Get connection arguments."""
        result = conninfo_to_dict(self.connection_string.get_secret_value()) if self.connection_string else {}

        if self.host:
            result["host"] = self.host
        if self.port:
            result["port"] = self.port
        if self.dbname:
            result["dbname"] = self.dbname
        if self.user:
            result["user"] = self.user
        if self.password:
            result["password"] = self.password.get_secret_value()

        return result

    async def create_connection_pool(
        self, connection_class: type["ACT"] | None = None, **kwargs: Any
    ) -> AsyncConnectionPool:
        """Creates a connection pool based off of settings.

        Args:
            connection_class: The connection class to use.
            kwargs: Additional keyword arguments to pass to the connection class.

        Returns:
            The connection pool.
        """
        try:
            # Only pass connection_class if it specified, or else allow psycopg to use the default connection class
            extra_args: dict[str, Any] = {} if connection_class is None else {"connection_class": connection_class}

            pool = AsyncConnectionPool(
                min_size=self.min_pool,
                max_size=self.max_pool,
                open=False,
                # kwargs are passed to the connection class
                kwargs={
                    **self.get_connection_args(),
                    **kwargs,
                },
                **extra_args,
            )
            await pool.open()
        except Exception as e:
            raise MemoryConnectorConnectionException("Error creating connection pool.") from e
        return pool


# region: Collection


@release_candidate
class PostgresCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """PostgreSQL collection implementation."""

    connection_pool: AsyncConnectionPool | None = None
    db_schema: str = DEFAULT_SCHEMA
    supported_key_types: ClassVar[set[str] | None] = {"str", "int"}
    supported_vector_types: ClassVar[set[str] | None] = {"float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}
    _distance_column_name: str = PrivateAttr(DISTANCE_COLUMN_NAME)

    _settings: PostgresSettings = PrivateAttr()
    """Postgres settings"""

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        connection_pool: AsyncConnectionPool | None = None,
        db_schema: str = DEFAULT_SCHEMA,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        settings: PostgresSettings | None = None,
        **kwargs: Any,
    ):
        """Initialize the collection.

        Args:
            record_type: The type of the data model.
            definition: The data model definition.
            collection_name: The name of the collection, which corresponds to the table name.
            embedding_generator: The embedding generator.
            connection_pool: The connection pool.
            db_schema: The database schema.
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            settings: The settings for creating a new connection pool. If not provided, the settings will be created
                from the environment.
            **kwargs: Additional arguments.
        """
        super().__init__(
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            embedding_generator=embedding_generator,
            connection_pool=connection_pool,
            db_schema=db_schema,
            # This controls whether the connection pool is managed by the collection
            # in the __aenter__ and __aexit__ methods.
            managed_client=connection_pool is None,
        )

        self._settings = settings or PostgresSettings(env_file_path=env_file_path, env_file_encoding=env_file_encoding)

    @override
    def model_post_init(self, __context: object | None = None) -> None:
        """Post-initialization of the model.

        In addition to the base class implementation, this method resets the distance column name
        to avoid collisions if necessary.
        """
        super().model_post_init(__context)

        distance_column_name = DISTANCE_COLUMN_NAME
        tries = 0
        while distance_column_name in self.definition.get_storage_names():
            # Reset the distance column name, ensuring no collision with existing model fields
            # Avoid bandit B311 - random is not used for a security/cryptographic purpose
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))  # nosec B311
            distance_column_name = f"{DISTANCE_COLUMN_NAME}_{suffix}"
            tries += 1
            if tries > 10:
                raise VectorStoreModelValidationError("Unable to generate a unique distance column name.")
        self._distance_column_name = distance_column_name

    @override
    async def __aenter__(self) -> "PostgresCollection":
        # If the connection pool was not provided, create a new one.
        if not self.connection_pool:
            self.connection_pool = await self._settings.create_connection_pool()
        return self

    @override
    async def __aexit__(self, *args):
        # Only close the connection pool if it was created by the collection.
        if self.managed_client and self.connection_pool:
            await self.connection_pool.close()
            # If the pool was created by the collection, set it to None to enable reusing the collection.
            if self.managed_client:
                self.connection_pool = None

    @override
    def _validate_data_model(self) -> None:
        """Validate the data model."""
        for field in self.definition.vector_fields:
            if field.dimensions is not None and field.dimensions > MAX_DIMENSIONALITY:
                raise VectorStoreModelValidationError(
                    f"Dimensionality of {field.dimensions} exceeds the maximum allowed value of {MAX_DIMENSIONALITY}."
                )

        super()._validate_data_model()

    @override
    async def _inner_upsert(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert records into the database.

        Args:
            records: The records, the format is specific to the store.
            **kwargs: Additional arguments, to be passed to the store.

        Returns:
            The keys of the upserted records.
        """
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        keys: MutableSequence[TKey] = []
        async with (
            self.connection_pool.connection() as conn,
            conn.transaction(),
            conn.cursor() as cur,
        ):
            # Split the records into batches
            max_rows_per_transaction = self._settings.max_rows_per_transaction
            for i in range(0, len(records), max_rows_per_transaction):
                record_batch = records[i : i + max_rows_per_transaction]

                fields = self.definition.fields

                row_values = [_convert_dict_to_row(record, fields) for record in record_batch]

                # Execute the INSERT statement for each batch
                await cur.executemany(
                    sql.SQL(
                        "INSERT INTO {schema}.{table} ({col_names}) VALUES ({placeholders}) "
                        "ON CONFLICT ({key_name}) DO UPDATE SET {update_columns}"
                    ).format(
                        schema=sql.Identifier(self.db_schema),
                        table=sql.Identifier(self.collection_name),
                        col_names=sql.SQL(", ").join(
                            sql.Identifier(field.storage_name or field.name) for field in fields
                        ),
                        placeholders=sql.SQL(", ").join(sql.Placeholder() * len(fields)),
                        key_name=sql.Identifier(self.definition.key_field_storage_name),
                        update_columns=sql.SQL(", ").join(
                            sql.SQL("{field} = EXCLUDED.{field}").format(
                                field=sql.Identifier(field.storage_name or field.name)
                            )
                            for field in fields
                            if field.name != self.definition.key_name
                        ),
                    ),
                    row_values,
                )
                keys.extend(
                    record[self.definition.key_field_storage_name]  # type: ignore
                    for record in record_batch
                )
        return keys

    @override
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> OneOrMany[dict[str, Any]] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        fields = [(field.storage_name or field.name, field) for field in self.definition.fields]
        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                sql.SQL("SELECT {select_list} FROM {schema}.{table} WHERE {key_name} IN ({keys})").format(
                    select_list=sql.SQL(", ").join(sql.Identifier(name) for (name, _) in fields),
                    schema=sql.Identifier(self.db_schema),
                    table=sql.Identifier(self.collection_name),
                    key_name=sql.Identifier(self.definition.key_field_storage_name),
                    keys=sql.SQL(", ").join(sql.Literal(key) for key in keys),
                )
            )
            rows = await cur.fetchall()
            if not rows:
                return None
            return [_convert_row_to_dict(row, fields) for row in rows]

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records with the given keys.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.
        """
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        async with (
            self.connection_pool.connection() as conn,
            conn.transaction(),
            conn.cursor() as cur,
        ):
            # Split the keys into batches
            max_rows_per_transaction = self._settings.max_rows_per_transaction
            for i in range(0, len(keys), max_rows_per_transaction):
                key_batch = keys[i : i + max_rows_per_transaction]

                # Execute the DELETE statement for each batch
                await cur.execute(
                    sql.SQL("DELETE FROM {schema}.{table} WHERE {name} IN ({keys})").format(
                        schema=sql.Identifier(self.db_schema),
                        table=sql.Identifier(self.collection_name),
                        name=sql.Identifier(self.definition.key_field_storage_name),
                        keys=sql.SQL(", ").join(sql.Literal(key) for key in key_batch),
                    )
                )

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Serialize a list of dicts of the data to the store model.

        Pass the records through without modification.
        """
        return records

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        """Deserialize the store models to a list of dicts.

        Pass the records through without modification.
        """
        return records

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create a PostgreSQL table based on a dictionary of VectorStoreRecordField.

        Args:
            table_name: Name of the table to be created
            fields: A dictionary where keys are column names and values are VectorStoreRecordField instances
            **kwargs: Additional arguments
        """
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        column_definitions = []
        table_name = self.collection_name

        for field in self.definition.fields:
            if not field.type_:
                raise ValueError(f"Property type is not defined for field '{field.name}'")

            # If the property type represents a Python type, convert it to a PostgreSQL type
            property_type = _python_type_to_postgres(field.type_) or field.type_.upper()

            # For Vector fields with dimensions, use pgvector's VECTOR type
            # Note that other vector types are supported in pgvector (e.g. halfvec),
            # but would need to be created outside of this method.
            if field.field_type == FieldTypes.VECTOR:
                column_definitions.append(
                    sql.SQL("{name} VECTOR({dimensions})").format(
                        name=sql.Identifier(field.storage_name or field.name),
                        dimensions=sql.Literal(field.dimensions),
                    )
                )
            elif field.field_type == FieldTypes.KEY:
                # Use the property_type directly for key fields
                column_definitions.append(
                    sql.SQL("{name} {col_type} PRIMARY KEY").format(
                        name=sql.Identifier(field.storage_name or field.name), col_type=sql.SQL(property_type)
                    )
                )
            else:
                # Use the property_type directly for other types
                column_definitions.append(
                    sql.SQL("{name} {col_type}").format(
                        name=sql.Identifier(field.storage_name or field.name), col_type=sql.SQL(property_type)
                    )
                )

        columns_str = sql.SQL(", ").join(column_definitions)

        create_table_query = sql.SQL("CREATE TABLE {schema}.{table} ({columns})").format(
            schema=sql.Identifier(self.db_schema), table=sql.Identifier(table_name), columns=columns_str
        )

        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(create_table_query)
            await conn.commit()

        logger.info(f"Postgres table '{table_name}' created successfully.")

        # If the vector field defines an index, apply it
        for vector_field in self.definition.vector_fields:
            await self._create_index(table_name, vector_field)

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                """,
                (self.db_schema, self.collection_name),
            )
            row = await cur.fetchone()
            return bool(row)

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Delete the collection."""
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                sql.SQL("DROP TABLE {schema}.{table} CASCADE").format(
                    schema=sql.Identifier(self.db_schema), table=sql.Identifier(self.collection_name)
                ),
            )
            await conn.commit()

    async def _create_index(self, table_name: str, vector_field: VectorStoreField) -> None:
        """Create an index on a column in the table.

        Args:
            table_name: The name of the table.
            vector_field: The vector field definition that the index is based on.
        """
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        if vector_field.distance_function not in DISTANCE_FUNCTION_MAP_STRING:
            raise VectorStoreOperationException(
                "Distance function must be set for HNSW indexes. "
                "Please set the distance function in the vector field definition."
            )

        if vector_field.index_kind not in INDEX_KIND_MAP:
            raise VectorStoreOperationException(
                f"Index kind '{vector_field.index_kind}' is not supported. "
                "Please set the index kind in the vector field definition."
            )

        column_name = vector_field.storage_name or vector_field.name
        index_name = f"{table_name}_{column_name}_idx"

        if (
            vector_field.index_kind == IndexKind.IVF_FLAT
            and vector_field.distance_function == DistanceFunction.MANHATTAN
        ):
            raise VectorStoreOperationException(
                "IVF_FLAT index is not supported with MANHATTAN distance function. "
                "Please use a different index kind or distance function or index kind."
            )

        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                sql.SQL("CREATE INDEX {index_name} ON {schema}.{table} USING {index_kind} ({column_name} {op})").format(
                    index_name=sql.Identifier(index_name),
                    schema=sql.Identifier(self.db_schema),
                    table=sql.Identifier(table_name),
                    index_kind=sql.SQL(INDEX_KIND_MAP[vector_field.index_kind]),
                    column_name=sql.Identifier(column_name),
                    op=sql.SQL(DISTANCE_FUNCTION_MAP_STRING[vector_field.distance_function]),
                )
            )
            await conn.commit()

        logger.info(f"Index '{index_name}' created successfully on column '{column_name}'.")

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )
        if not vector:
            vector = await self._generate_vector_from_values(values, options, **kwargs)
        if not vector:
            raise VectorStoreOperationException("No vector provided and no values to generate a vector from.")

        if vector is not None:
            query, params, return_fields = self._construct_vector_query(vector, options, **kwargs)

        if options.include_total_count:
            async with self.connection_pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                # Fetch all results to get total count.
                rows = await cur.fetchall()
                row_dicts = [_convert_row_to_dict(row, return_fields) for row in rows]
                return KernelSearchResults(
                    results=self._get_vector_search_results_from_results(row_dicts, options), total_count=len(row_dicts)
                )
        else:
            # Use an asynchronous generator to fetch and yield results
            connection_pool = self.connection_pool

            async def fetch_results() -> AsyncGenerator[dict[str, Any], None]:
                async with connection_pool.connection() as conn, conn.cursor() as cur:
                    await cur.execute(query, params)
                    async for row in cur:
                        yield _convert_row_to_dict(row, return_fields)

            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(fetch_results(), options),
                total_count=None,
            )

    def _construct_vector_query(
        self,
        vector: Sequence[float | int],
        options: VectorSearchOptions,
        **kwargs: Any,
    ) -> tuple[sql.Composed, list[Any], list[tuple[str, VectorStoreField | None]]]:
        """Construct a vector search query.

        Args:
            vector: The vector to search for.
            options: The search options.
            **kwargs: Additional arguments.

        Returns:
            The query, parameters, and the fields representing the columns in the result.
        """
        # Get the vector field we will be searching against,
        # defaulting to the first vector field if not specified
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreOperationException(
                f"Vector field '{options.vector_property_name}' not found in the data model."
            )

        if vector_field.distance_function not in DISTANCE_FUNCTION_MAP_OPS:
            raise VectorStoreOperationException(
                f"Distance function '{vector_field.distance_function}' is not supported. "
                "Please set the distance function in the vector field definition."
            )

        # Select all fields except all vector fields if include_vectors is False
        select_list = self.definition.get_storage_names(include_vector_fields=options.include_vectors)
        query = sql.SQL("SELECT {select_list}, {vec_col} {dist_op} %s as {dist_col} FROM {schema}.{table}").format(
            select_list=sql.SQL(", ").join(sql.Identifier(name) for name in select_list),
            vec_col=sql.Identifier(vector_field.storage_name or vector_field.name),
            dist_op=sql.SQL(DISTANCE_FUNCTION_MAP_OPS[vector_field.distance_function]),
            dist_col=sql.Identifier(self._distance_column_name),
            schema=sql.Identifier(self.db_schema),
            table=sql.Identifier(self.collection_name),
        )

        if where_clauses := self._build_filter(options.filter):  # type: ignore
            query += (
                sql.SQL("WHERE {clause}").format(clause=sql.SQL(" AND ").join(where_clauses))
                if isinstance(where_clauses, list)
                else sql.SQL("WHERE {clause}").format(clause=where_clauses)
            )

        query += sql.SQL(" ORDER BY {dist_col} LIMIT {limit}").format(
            dist_col=sql.Identifier(self._distance_column_name),
            limit=sql.Literal(options.top),
        )

        if options.skip:
            query += sql.SQL(" OFFSET {offset}").format(offset=sql.Literal(options.skip))

        # For cosine similarity, we need to take 1 - cosine distance.
        # However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        # Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if vector_field.distance_function == DistanceFunction.COSINE_SIMILARITY:
            query = sql.SQL(
                "SELECT subquery.*, 1 - subquery.{subquery_dist_col} AS {dist_col} FROM ({subquery}) AS subquery"
            ).format(
                subquery_dist_col=sql.Identifier(self._distance_column_name),
                dist_col=sql.Identifier(self._distance_column_name),
                subquery=query,
            )

        # For inner product, we need to take -1 * inner product.
        # However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        # Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if vector_field.distance_function == DistanceFunction.DOT_PROD:
            query = sql.SQL(
                "SELECT subquery.*, -1 * subquery.{subquery_dist_col} AS {dist_col} FROM ({subquery}) AS subquery"
            ).format(
                subquery_dist_col=sql.Identifier(self._distance_column_name),
                dist_col=sql.Identifier(self._distance_column_name),
                subquery=query,
            )

        # Convert the vector to a string for the query
        params = ["[" + ",".join([str(float(v)) for v in vector]) + "]"]

        return (
            query,
            params,
            [
                *(
                    (field.storage_name or field.name, field)
                    for field in self.definition.fields
                    if field.storage_name or field.name in select_list
                ),
                (self._distance_column_name, None),
            ],
        )

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        # Comparison operations
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., 1 < x < 3) become AND of each comparison
                    values = []
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right = node.comparators[idx]
                        op = node.ops[idx]
                        values.append(self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right])))
                    return f"({' AND '.join(values)})"
                left = self._lambda_parser(node.left)
                right = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.In():
                        return f"{left} IN {right}"
                    case ast.NotIn():
                        return f"{left} NOT IN {right}"
                    case ast.Eq():
                        return f"{left} = {right}"
                    case ast.NotEq():
                        return f"{left} <> {right}"
                    case ast.Gt():
                        return f"{left} > {right}"
                    case ast.GtE():
                        return f"{left} >= {right}"
                    case ast.Lt():
                        return f"{left} < {right}"
                    case ast.LtE():
                        return f"{left} <= {right}"
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op = node.op  # type: ignore
                values = [self._lambda_parser(v) for v in node.values]
                if isinstance(op, ast.And):
                    return f"({' AND '.join(values)})"
                if isinstance(op, ast.Or):
                    return f"({' OR '.join(values)})"
                raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        operand = self._lambda_parser(node.operand)
                        return f"NOT ({operand})"
                    case ast.UAdd() | ast.USub() | ast.Invert():
                        raise NotImplementedError("Unary +, -, ~ are not supported in PostgreSQL filters.")
            case ast.Attribute():
                # Only allow attributes that are in the data model
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return f'"{node.attr}"'
            case ast.Name():
                # Only allow names that are in the data model
                if node.id not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.id}' not in data model (storage property names are used)."
                    )
                return f'"{node.id}"'
            case ast.Constant():
                if isinstance(node.value, str):
                    return "'" + node.value.replace("'", "''") + "'"
                if node.value is None:
                    return "NULL"
                if isinstance(node.value, bool):
                    return "TRUE" if node.value else "FALSE"
                return str(node.value)
            case ast.List():
                # For IN/NOT IN lists
                return "(" + ", ".join(self._lambda_parser(elt) for elt in node.elts) + ")"
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return {k: v for (k, v) in result.items() if k != self._distance_column_name}

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.pop(self._distance_column_name, None)


# region: Store


@release_candidate
class PostgresStore(VectorStore):
    """PostgreSQL store implementation."""

    connection_pool: AsyncConnectionPool
    db_schema: str = DEFAULT_SCHEMA
    tables: list[str] | None = None
    """Tables to consider as collections. Default is all tables in the schema."""

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            base_query = sql.SQL("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = {}
            """).format(sql.Placeholder())

            params = [self.db_schema]

            if self.tables:
                table_placeholders = sql.SQL(", ").join(sql.Placeholder() * len(self.tables))
                base_query += sql.SQL(" AND table_name IN ({})").format(table_placeholders)
                params.extend(self.tables)

            await cur.execute(base_query, params)
            rows = await cur.fetchall()
            return [row[0] for row in rows]

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> PostgresCollection:
        return PostgresCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator or self.embedding_generator,
            connection_pool=self.connection_pool,
            db_schema=self.db_schema,
            **kwargs,
        )
