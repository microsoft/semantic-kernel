# Copyright (c) 2025, Oracle Corporation. All rights reserved. # noqa: CPY001

# Standard Library
import array
import ast
import datetime
import logging
import re
import sys
import uuid
from collections.abc import AsyncIterable, Mapping, Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar

# Third-party Libraries
import numpy as np
import oracledb
from pydantic import Field, PrivateAttr, SecretStr

# Semantic Kernel AI and Data Abstractions
from semantic_kernel.connectors.ai.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.data.vector import (
    DistanceFunction,
    GetFilteredRecordOptions,
    IndexKind,
    KernelSearchResults,
    SearchType,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    VectorStoreField,
)

# Semantic Kernel Exceptions
from semantic_kernel.exceptions import (
    MemoryConnectorConnectionException,
    VectorSearchExecutionException,
    VectorStoreOperationException,
)

# Semantic Kernel Utilities & Config
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate

oracledb.defaults.fetch_lobs = False

# Compatibility: @override decorator
# Python 3.12+ has typing.override natively,
# for older versions use typing_extensions.
if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

# Type variables for generics
TKey = TypeVar("TKey", bound=str | int | uuid.UUID)
TModel = TypeVar("TModel")

# Module-level logger
logger = logging.getLogger(__name__)

# Explicit module exports:
# Only expose high-level entry points; keep helpers internal.
__all__ = [
    "OracleSettings",
    "OracleStore",
]

# Environment Variable keys for Oracle DB configuration
POOL_MIN_ENV_VAR: Final[str] = "ORACLE_POOL_MIN"
POOL_MAX_ENV_VAR: Final[str] = "ORACLE_POOL_MAX"
POOL_INCREMENT_ENV_VAR: Final[str] = "ORACLE_POOL_INCREMENT"

# Maps Semantic Kernel enums to Oracle SQL keywords
DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_DISTANCE: "COSINE",
    DistanceFunction.EUCLIDEAN_DISTANCE: "EUCLIDEAN",
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: "EUCLIDEAN_SQUARED",
    DistanceFunction.DOT_PROD: "DOT",
    DistanceFunction.HAMMING: "HAMMING",
    DistanceFunction.MANHATTAN: "MANHATTAN",
    DistanceFunction.DEFAULT: "COSINE",
}

# Maps index kind enums to Oracle SQL keywords
INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {IndexKind.HNSW: "HNSW", IndexKind.IVF_FLAT: "IVF"}

# Maps dtype strings to NumPy types and array codes
KIND_MAP = {
    "float32": (np.float32, "f"),
    "float": (np.float64, "d"),
    "float64": (np.float64, "d"),
    "int8": (np.int8, "b"),
    "uint8": (np.uint8, "B"),
    "binary": (np.uint8, "B"),
}

VECTOR_TYPE_MAPPING: dict[str, str] = {
    "uint8": "BINARY",
    "int8": "INT8",
    "float": "FLOAT64",
    "float32": "FLOAT32",
    "float64": "FLOAT64",
    "binary": "BINARY",
}

# helper methods


def _map_scalar_field_type_to_oracle(field_type_str: str) -> str | None:
    """Map a Semantic Kernel record *scalar field* type (key or data).

    This is used when generating table DDL for all non-vector fields,
    including primary keys and data fields.

    Args:
        field_type_str: The field type as a string
            (e.g., 'int', 'float', 'uuid', 'dict', 'bytes').

    Returns:
        The corresponding Oracle SQL column type as a string,
        or None if there is no known mapping.
    """
    type_mapping = {
        "bool": "BOOLEAN",
        "byte": "NUMBER(3)",
        "int": "NUMBER(10)",
        "long": "NUMBER(19)",
        "float": "BINARY_FLOAT",
        "double": "BINARY_DOUBLE",
        "Decimal": "NUMBER",
        "UUID": "RAW(16)",
        "date": "DATE",
        "datetime": "TIMESTAMP",
        "timedelta": "INTERVAL DAY TO SECOND",
        "bytes": "RAW(2000)",
        "dict": "JSON",
        "clob": "CLOB",
        "blob": "BLOB",
    }

    list_pattern = re.compile(r"list\[(.*)\]")
    if list_pattern.match(field_type_str):
        return "JSON"

    dict_pattern = re.compile(r"dict\[(.*?),\s*(.*?)\]")
    if dict_pattern.match(field_type_str):
        return "JSON"

    str_match = re.match(r"str(?:\((\d+)\))?$", field_type_str)
    if str_match:
        size = str_match.group(1) or "4000"
        return f"VARCHAR2({size})"

    if field_type_str not in type_mapping:
        raise VectorStoreOperationException(f"Unsupported scalar field type: {field_type_str}")

    return type_mapping.get(field_type_str)


def _sk_vector_element_to_oracle(field_type_str: str) -> str | None:
    """Convert a Semantic Kernel vector element type string to an Oracle VECTOR element type string."""
    list_pattern = re.compile(r"(?i)^list\[(.*)\]$")
    field_type = field_type_str.strip()

    # Iteratively unwrap list[...] until no longer matches
    while True:
        match = list_pattern.match(field_type)
        if not match:
            break
        field_type = match.group(1).strip()

    # Return final mapped type if available
    return VECTOR_TYPE_MAPPING.get(field_type)


class BindCounter:
    """Helper class to generate unique bind variable names for SQL queries."""

    def __init__(self, start: int = 1):
        self._index = start

    def next_bind(self) -> str:
        name = f"bind_val{self._index}"
        self._index += 1
        return name


# region: Oracle Settings


@release_candidate
class OracleSettings(KernelBaseSettings):
    """Oracle connector settings.

    This class is used to configure the Oracle connection pool
    and related options for the Oracle vector or memory store connectors.

    It supports both standard username/password authentication and
    wallet-based secure connections, and is compatible with Oracle's
    native async driver (python-oracledb) for efficient async operations.

    The settings align with common Oracle client environment variables
    such as ORACLE_USER, ORACLE_PASSWORD, and ORACLE_CONNECTION_STRING,
    while following the Semantic Kernel convention for configuration
    through environment variables or explicit keyword arguments.

    Args:
        user: Oracle database username.
            (Env var ORACLE_USER)
        password: Oracle database password.
            (Env var ORACLE_PASSWORD)
        connection_string: Full Oracle connection string, for example:
            "host:port/service_name".
            (Env var ORACLE_CONNECTION_STRING)
        min: Minimum number of connections in the pool.
            (Env var ORACLE_MIN)
        max: Maximum number of connections in the pool.
            (Env var ORACLE_MAX)
        increment: Number of connections to add when the pool grows.
            (Env var ORACLE_INCREMENT)
        wallet_location: Path to the Oracle wallet directory for wallet-based authentication.
            (Env var ORACLE_WALLET_LOCATION)
        wallet_password: Password for the Oracle wallet.
            (Env var ORACLE_WALLET_PASSWORD)
        connection_pool: Optional preconfigured AsyncConnectionPool instance.
    """

    env_prefix: ClassVar[str] = "ORACLE_"
    user: str | None = None
    password: SecretStr | None = None
    connection_string: str | None = None
    min: int | None = Field(default=None, validation_alias=POOL_MIN_ENV_VAR)
    max: int | None = Field(default=None, validation_alias=POOL_MAX_ENV_VAR)
    increment: int | None = Field(default=None, validation_alias=POOL_INCREMENT_ENV_VAR)
    wallet_location: str | None = None
    wallet_password: SecretStr | None = None

    _connection_pool: oracledb.AsyncConnectionPool | None = PrivateAttr(default=None)

    async def create_connection_pool(self, **kwargs: Any) -> oracledb.AsyncConnectionPool:
        """Creates an async Oracle connection pool."""
        try:
            # Create pool with extra user-supplied kwargs
            self._connection_pool = oracledb.create_pool_async(
                user=self.user,
                password=self.password.get_secret_value() if self.password else None,
                dsn=self.connection_string,
                wallet_location=self.wallet_location,
                wallet_password=self.wallet_password.get_secret_value() if self.wallet_password else None,
                min=self.min,
                max=self.max,
                increment=self.increment,
                **kwargs,  # extra pool params
            )

        except Exception as err:
            raise MemoryConnectorConnectionException("Error creating Oracle connection pool.") from err

        return self._connection_pool


# region: Oracle Collections


@release_candidate
class OracleCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """Oracle implementation of VectorStoreCollection + VectorSearch."""

    connection_pool: oracledb.AsyncConnectionPool | None = None
    db_schema: str | None = None
    pool_args: dict[str, Any] | None = None
    supported_key_types: ClassVar[set[str] | None] = {"str", "int", "UUID"}
    supported_vector_types: ClassVar[set[str] | None] = set(VECTOR_TYPE_MAPPING.keys())
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}
    _distance_column_name: str = "SIMILARITY_SKOVS"

    def __init__(
        self,
        record_type: type[TModel],
        collection_name: str | None = None,
        definition: VectorStoreCollectionDefinition | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        connection_pool: oracledb.AsyncConnectionPool | None = None,
        db_schema: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        settings: OracleSettings | None = None,
        pool_args: dict[str, Any] | None = None,
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
            pool_args: Optional dict of additional arguments to configure the connection pool
                (e.g., timeout, ping_interval).
            **kwargs: Additional arguments.
        """
        # Build settings from env if we need to manage our own pool
        settings = settings or OracleSettings(
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )
        managed_client = False

        # Create pool if missing
        if connection_pool is None:
            try:
                pool_args = pool_args or {}
                connection_pool = oracledb.create_pool_async(
                    user=settings.user,
                    password=settings.password.get_secret_value() if settings.password else None,
                    dsn=settings.connection_string,
                    wallet_location=settings.wallet_location,
                    wallet_password=settings.wallet_password.get_secret_value() if settings.wallet_password else None,
                    min=settings.min,
                    max=settings.max,
                    increment=settings.increment,
                    **pool_args,
                )
            except Exception as err:
                raise MemoryConnectorConnectionException("Error creating Oracle connection pool.") from err

            managed_client = True
        else:
            managed_client = False

        super().__init__(
            collection_name=collection_name,  # type: ignore
            record_type=record_type,
            definition=definition,  # type: ignore
            embedding_generator=embedding_generator,
            connection_pool=connection_pool,  # type: ignore
            db_schema=db_schema,  # type: ignore
            settings=settings,  # type: ignore
            # This controls whether the connection pool is managed by the collection
            # in the __aenter__ and __aexit__ methods.
            managed_client=managed_client,
        )

        # Compute UUID field names once
        self._uuid_fields = [
            field.storage_name or field.name
            for field in (*self.definition.data_fields, self.definition.key_field)
            if field.type_ == "UUID"
        ]

        # Validate key/data/vector field once per life-cycle
        key_field = self.definition.key_field
        key_field_name = key_field.storage_name or key_field.name
        self._validate_identifiers(key_field_name)

        for field in self.definition.data_fields:
            data_field_name = field.storage_name or field.name
            self._validate_identifiers(data_field_name)

        for field in self.definition.vector_fields:
            vector_field_name = field.storage_name or field.name
            self._validate_identifiers(vector_field_name)

            dtype = field.type_ or "float32"
            if dtype not in KIND_MAP:
                raise VectorStoreOperationException(
                    f"Unsupported dtype '{dtype}' for field '{field.name}'. "
                    f"Supported dtypes: {', '.join(KIND_MAP.keys())}"
                )

    @override
    async def __aenter__(self) -> "OracleCollection":
        return self

    @override
    async def __aexit__(self, *args: Any) -> None:
        # Only close the connection pool if it was created by the collection itself.
        if self.managed_client and self.connection_pool:
            try:
                await self.connection_pool.close()
            except Exception as e:
                logger.warning("Error closing Oracle connection pool: %s", e)
            finally:
                self.connection_pool = None
                self.managed_client = False

    def _check_pool(self) -> oracledb.AsyncConnectionPool:
        """Ensure that the connection pool is available, otherwise raise a consistent error."""
        if self.connection_pool is None:
            raise VectorStoreOperationException("Collection has no connection pool.")
        return self.connection_pool

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        """Deserialize the store models to a list of dicts. Pass the records through without modification."""
        return records

    def _full_table_name(self) -> str:
        """Return the fully qualified table name with optional schema prefix, quoted."""
        self._validate_identifiers(self.collection_name)
        if self.db_schema:
            self._validate_identifiers(self.db_schema)
            return f'"{self.db_schema}"."{self.collection_name}"'
        return f'"{self.collection_name}"'

    async def _get_connection(self):
        """Acquire a connection from the pool, ensuring input/output type handlers are always set.

        Raises VectorStoreOperationException if no connection pool is configured.
        """
        pool = self._check_pool()
        conn = await pool.acquire()
        # if you only want to set these in certain circumstances you can add a parameter to
        # the function for that purpose but it should be safe to set at all times
        conn.inputtypehandler = self._input_type_handler
        conn.outputtypehandler = self._output_type_handler
        return conn

    def _input_type_handler(self, cursor, value, arraysize):
        """Map Python types to Oracle bind variables with correct DB types."""
        if isinstance(value, np.ndarray):
            return cursor.var(oracledb.DB_TYPE_VECTOR, arraysize=arraysize, inconverter=self._numpy_converter_in)

        if isinstance(value, uuid.UUID):
            return cursor.var(oracledb.DB_TYPE_RAW, arraysize=arraysize, inconverter=lambda v: v.bytes)

        if isinstance(value, (dict, list)):
            return cursor.var(oracledb.DB_TYPE_JSON, arraysize=arraysize)

        if isinstance(value, bytes):
            return cursor.var(oracledb.DB_TYPE_RAW, arraysize=arraysize)

        return None

    def _numpy_converter_in(self, value):
        """Convert a NumPy array into a Python array.array compatible with Oracle DB_TYPE_VECTOR."""
        dtype_name = value.dtype.name
        np_dtype, code = KIND_MAP[dtype_name]
        value = value.astype(np_dtype, copy=False)
        return array.array(code, value)

    def _output_type_handler(self, cursor, metadata):
        """Map Oracle DB column types to Python-native objects during fetch operations."""
        # VECTOR columns to list
        if metadata.type_code == oracledb.DB_TYPE_VECTOR:
            return cursor.var(oracledb.DB_TYPE_VECTOR, arraysize=cursor.arraysize, outconverter=lambda arr: list(arr))

        # RAW to UUID
        if metadata.type_code == oracledb.DB_TYPE_RAW and metadata.name in self._uuid_fields:
            return cursor.var(
                oracledb.DB_TYPE_RAW,
                arraysize=cursor.arraysize,
                outconverter=lambda b: uuid.UUID(bytes=b) if b is not None else None,
            )

        return None

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Serialize a list of dicts of the data to the store model. Pass the records through without modification."""
        return records

    def _validate_identifiers(self, name: str) -> None:
        """Validate Oracle identifier to disallow embedded double quotes.

        Since quoted identifiers are not allowed, any double quote is invalid.
        """
        if not name:
            raise VectorStoreOperationException("Identifier cannot be empty")

        if '"' in name:
            raise VectorStoreOperationException(f"Invalid identifier with quotes: {name}")

    def _build_check_table_exists_query(self) -> tuple[str, dict[str, str]]:
        """Build SQL + bind variables for checking table existence.

        - If schema is provided, query ALL_TABLES.
        - If no schema, query USER_TABLES.
        """
        if self.db_schema:
            sql = """
                SELECT 1
                FROM   all_tables
                WHERE  owner = :owner
                AND    table_name = :tbl
            """
            bind_vars = {
                "owner": self.db_schema,
                "tbl": self.collection_name,
            }
        else:
            sql = """
                SELECT 1
                FROM   user_tables
                WHERE  table_name = :tbl
            """
            bind_vars = {"tbl": self.collection_name}

        return sql, bind_vars

    @override
    async def collection_exists(self, **kwargs: Any) -> bool:
        """Return True if the table backing this collection exists."""
        pool = self._check_pool()

        sql, binds = self._build_check_table_exists_query()
        async with pool.acquire() as conn:
            result = await conn.fetchone(sql, binds)
            return result is not None

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Deletes collection if it exists."""
        pool = self._check_pool()
        tbl = self._full_table_name()
        drop_sql = f"DROP TABLE IF EXISTS {tbl} CASCADE CONSTRAINTS PURGE"

        async with pool.acquire() as conn:
            await conn.execute(drop_sql)
            logger.debug(f"Oracle table '{self.collection_name}' deleted successfully.")

    def _build_create_table_query(
        self,
        *,
        table: str,
        key_field: VectorStoreField,
        data_fields: list[VectorStoreField],
        vector_fields: list[VectorStoreField],
    ) -> str:
        col_lines: list[str] = []

        if not key_field.type_:
            raise VectorStoreOperationException(f"Type missing for key field '{key_field.name}'")

        pk_name = key_field.storage_name or key_field.name
        col_lines.append(f'"{pk_name}" {_map_scalar_field_type_to_oracle(key_field.type_)} PRIMARY KEY')

        for f in data_fields:
            if not f.type_:
                raise VectorStoreOperationException(f"Type missing for data field '{f.name}'")

            sql_type = _map_scalar_field_type_to_oracle(f.type_)
            if sql_type is None:
                raise VectorStoreOperationException(f'Unsupported Oracle type for field "{f.name}" ({f.type_})')

            col_name = f.storage_name or f.name
            col_lines.append(f'"{col_name}" {sql_type}')

        for f in vector_fields:
            if not f.type_ or f.dimensions is None:
                raise VectorStoreOperationException(f"Vector field '{f.name}' missing type or dimensions")

            col_name = f.storage_name or f.name
            col_lines.append(f'"{col_name}" VECTOR({f.dimensions} , {_sk_vector_element_to_oracle(f.type_)})')

        columns_sql = ",\n  ".join(col_lines)
        return f"CREATE TABLE IF NOT EXISTS {table} (\n  {columns_sql}\n)"

    def _create_vector_index(self, table_name: str, vector_field: VectorStoreField) -> str | None:
        """Build a CREATE VECTOR INDEX statement for an Oracle vector column using HNSW or IVF indexing."""
        if vector_field.index_kind not in INDEX_KIND_MAP:
            logger.warning(
                f"Index kind '{vector_field.index_kind}' is not supported. "
                "Please set the index kind in the vector field definition."
            )
            return None

        if not vector_field.distance_function or vector_field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function '{vector_field.distance_function}' is not supported. "
                "Please set the distance function in the vector field definition."
            )
        distance = DISTANCE_FUNCTION_MAP[vector_field.distance_function]

        column = vector_field.storage_name or vector_field.name
        last_token = table_name.split(".")[-1]
        base_table = last_token.strip('"')
        index_name = f'"{base_table}_{column}_idx"'
        index_kind = vector_field.index_kind
        if index_kind == IndexKind.HNSW or index_kind == IndexKind.DEFAULT:
            index_subtype = f"ORGANIZATION INMEMORY NEIGHBOR GRAPH DISTANCE {distance} "
        else:
            # IndexKind.IVF_FLAT
            index_subtype = f"ORGANIZATION NEIGHBOR PARTITIONS DISTANCE {distance} "

        return f'CREATE VECTOR INDEX IF NOT EXISTS {index_name}\nON {table_name} ("{column}")\n{index_subtype}'

    def _create_data_index(self, table_name: str, field) -> str | None:
        """Build a CREATE INDEX statement for a single data field if it is indexable.

        Returns the SQL string or None if no index should be created.
        """
        if not getattr(field, "is_indexed", False):
            return None

        oracle_type = _map_scalar_field_type_to_oracle(field.type_) if field.type_ else None
        if oracle_type and oracle_type.lower() != "json":
            col = field.storage_name or field.name
            last_token = table_name.split(".")[-1]
            base_table = last_token.strip('"')
            index_name = f'"{base_table}_{col}_idx"'
            return f'CREATE INDEX {index_name} ON {table_name} ("{col}" ASC)'
        return None

    @override
    async def ensure_collection_exists(self, **kwargs: Any) -> None:
        """Create the table (and vector indexes) if not existing."""
        pool = self._check_pool()
        tbl = self._full_table_name()
        create_sql = self._build_create_table_query(
            table=tbl,
            key_field=self.definition.key_field,
            data_fields=self.definition.data_fields,
            vector_fields=self.definition.vector_fields,
        )

        # Combine create table + vector + data indexes
        statements = (
            [create_sql]
            + [stmt for vf in self.definition.vector_fields if (stmt := self._create_vector_index(tbl, vf))]
            + [stmt for field in self.definition.data_fields if (stmt := self._create_data_index(tbl, field))]
        )

        async with pool.acquire() as conn:
            for statement in statements:
                await conn.execute(statement)
            await conn.commit()
        logger.info(f"Oracle table '{self.collection_name}' created successfully.")

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records whose primary keys are in ``keys``."""
        pool = self._check_pool()
        if not keys:
            return

        tbl = self._full_table_name()
        pk_col = self.definition.key_field.storage_name or self.definition.key_field.name
        delete_sql = f'DELETE FROM {tbl} WHERE "{pk_col}" = :1'  # nosec B608

        async with pool.acquire() as conn:
            binds = [(k,) for k in keys]
            await conn.executemany(delete_sql, binds)
            await conn.commit()

    def _build_select_query(
        self,
        table: str,
        key_field: VectorStoreField,
        data_fields: list[VectorStoreField],
        vector_fields: list[VectorStoreField],
        keys: Sequence[Any] | None,
        options: GetFilteredRecordOptions | None,
        include_vectors: bool = False,
    ) -> tuple[str, list[Any]]:
        # SELECT clause
        all_fields = [key_field, *data_fields, *vector_fields] if include_vectors else [key_field, *data_fields]
        field_lookup = {f.name: f for f in all_fields}
        select_clause = ", ".join(f'"{f.storage_name or f.name}" AS "{f.name}"' for f in all_fields)

        sql = f"SELECT {select_clause} FROM {table}"  # nosec B608
        bind_values: list[Any] = []

        # WHERE clause by keys
        if keys:
            placeholders = ", ".join(f":{i + 1}" for i in range(len(keys)))
            sql += f' WHERE "{key_field.storage_name or key_field.name}" IN ({placeholders})'
            bind_values.extend(keys)

        # ORDER BY
        if options and options.order_by:
            parts: list[str] = []
            for logical_name, asc in options.order_by.items():
                field = field_lookup[logical_name]
                field_name = field.storage_name or field.name
                direction = "ASC" if asc else "DESC"
                parts.append(f'"{field_name}" {direction}')
            sql += " ORDER BY " + ", ".join(parts)

        # Pagination
        if options:
            if options.skip is not None:
                sql += f" OFFSET {options.skip} ROWS"
            if options.top is not None:
                sql += f" FETCH NEXT {options.top} ROWS ONLY"

        return sql, bind_values

    @override
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> OneOrMany[dict[str, Any]] | None:
        """Retrieve one or more records from the Oracle table.

        Returns:
        OneOrMany[dict[str, Any]] | None
            - A single record (dict) when exactly one row matches
            - A list of dicts when multiple rows match
            - ``None`` when no rows match
        """
        pool = self._check_pool()
        if not keys and options is None:
            return None

        table = self._full_table_name()
        include_vectors = kwargs.get("include_vectors", True)
        q, binds = self._build_select_query(
            table,
            self.definition.key_field,
            self.definition.data_fields,
            self.definition.vector_fields,
            keys,
            options,
            include_vectors,
        )

        async with pool.acquire() as conn:
            conn.outputtypehandler = self._output_type_handler
            rows = await conn.fetchall(q, binds)

        # Build column list once: key, data, then vector fields
        columns = [self.definition.key_field.name] + [f.name for f in self.definition.data_fields]
        if include_vectors:
            columns = columns + [f.name for f in self.definition.vector_fields]

        if not rows:
            return None

        # build list of dict records
        records: list[dict[str, Any]] = []
        for row in rows:
            record = {col: val for col, val in zip(columns, row)}
            records.append(record)

        return records[0] if len(records) == 1 else records

    def _convert_dict_to_row(
        self,
        record: Mapping[str, Any],
        fields: Sequence[VectorStoreField],
    ) -> tuple[Any, ...]:
        """Convert an in-memory record (dict) into a positional tuple ready for executemany() with Oracle."""
        row: list[Any] = []

        for field in fields:
            column_name = field.name
            value = record.get(column_name)
            if value is None:
                row.append(None)
                continue

            if field.field_type == "vector" and isinstance(value, (list)):
                _, code = KIND_MAP[field.type_]  # type: ignore[index]
                value = array.array(code, value)
                row.append(value)
                continue
            row.append(value)

        return tuple(row)

    def _build_single_merge_query(
        self,
        table_name: str,
        key_field: VectorStoreField,
        data_fields: list[VectorStoreField],
        vector_fields: list[VectorStoreField],
    ) -> str:
        """Build a parameterised MERGE statement for Oracle.

        One executemany() call executes this MERGE once per record.
        """
        all_fields = [key_field, *data_fields, *vector_fields]
        src_bindings = ",\n     ".join(
            f':{idx + 1} AS "{field.storage_name or field.name}"' for idx, field in enumerate(all_fields)
        )

        # When matched then update data
        update_clause = ",\n     ".join(
            f't."{field.storage_name or field.name}" = s."{field.storage_name or field.name}"'
            for field in data_fields + vector_fields
        )

        # When not matched then insert data
        insert_columns = ", ".join(f'"{field.storage_name or field.name}"' for field in all_fields)
        insert_values = ", ".join(f's."{field.storage_name or field.name}"' for field in all_fields)

        merge_sql = f"""
            MERGE INTO {table_name} t
            USING (
                SELECT {src_bindings}
                FROM dual
            ) s
            ON (
                t."{key_field.storage_name or key_field.name}" = s."{key_field.storage_name or key_field.name}"
            )
            WHEN MATCHED THEN
                UPDATE SET {update_clause}
            WHEN NOT MATCHED THEN
                INSERT ({insert_columns})
                VALUES ({insert_values})
        """  # nosec B608
        return merge_sql.strip()

    @override
    async def _inner_upsert(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        pool = self._check_pool()
        if not records:
            return []

        key_field = self.definition.key_field
        data_fields = self.definition.data_fields
        vector_fields = self.definition.vector_fields
        table_name = self._full_table_name()
        ordered_fields = [key_field, *data_fields, *vector_fields]
        query = self._build_single_merge_query(table_name, key_field, data_fields, vector_fields)

        async with pool.acquire() as conn:
            conn.inputtypehandler = self._input_type_handler
            binds = [self._convert_dict_to_row(record, ordered_fields) for record in records]
            await conn.executemany(query, binds)
            await conn.commit()

        return [record[key_field.name] for record in records]

    def _build_search_query(
        self,
        table: str,
        key_field: VectorStoreField,
        data_fields: list[VectorStoreField],
        vector_fields: list[VectorStoreField],
        vector: Sequence[float | int],
        vector_field: VectorStoreField,
        options: VectorSearchOptions,
        filter_clause: str | None,
    ) -> tuple[str, list[Any], list[str]]:
        bind_values = []
        bind_index = 1

        # Vector bind placeholder
        vector_placeholder = f":{bind_index}"
        bind_values.append(vector)
        bind_index += 1

        # Build TO_VECTOR() expression from field metadata
        dim = vector_field.dimensions or len(vector)
        # Normalize user-provided dtype and map to Oracle-supported VECTOR types.
        raw_dtype = (vector_field.type_ or "float32").lower()

        dtype = VECTOR_TYPE_MAPPING.get(raw_dtype, "FLOAT32")

        to_vector_expr = f"TO_VECTOR({vector_placeholder}, {dim}, {dtype})"

        # Fields to SELECT
        select_fields = [f'"{key_field.storage_name or key_field.name}"'] + [
            f'"{field.storage_name or field.name}"' for field in data_fields
        ]
        if options.include_vectors:
            select_fields += [f'"{f.storage_name or f.name}"' for f in vector_fields]

        select_clause = ", ".join(select_fields)

        # Choose distance function
        if not vector_field.distance_function or vector_field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function '{vector_field.distance_function}' is not supported. "
                "Please set the distance function in the vector field definition."
            )
        distance_fn = DISTANCE_FUNCTION_MAP[vector_field.distance_function]
        distance_expr = (
            f'VECTOR_DISTANCE("{vector_field.storage_name or vector_field.name}", '
            f'{to_vector_expr}, {distance_fn}) AS "{self._distance_column_name}"'
        )

        # Final SQL assembly
        sql = f"""
            SELECT {select_clause}, {distance_expr}
            FROM {table}
        """.strip()  # nosec B608

        if filter_clause:
            sql += f"\nWHERE {filter_clause}"

        sql += f'\nORDER BY "{self._distance_column_name}" ASC'
        if options:
            if options.skip is not None:
                sql += f" OFFSET {options.skip} ROWS"
            if options.top is not None:
                sql += f" FETCH NEXT {options.top} ROWS ONLY"
        return sql, bind_values, select_fields

    async def _fetch_records(self, sql: str, binds: list[Any]) -> AsyncIterable[dict[str, Any]]:
        """Execute the SQL with binds and yield rows as dictionaries mapping column name to value.

        Uses zip() for clean row-to-dict mapping.
        """
        async with await self._get_connection() as conn:
            conn.inputtypehandler = self._input_type_handler
            conn.outputtypehandler = self._output_type_handler
            with conn.cursor() as cur:
                await cur.execute(sql, binds)
                col_names = [d.name for d in cur.description]
                async for row in cur:
                    yield dict(zip(col_names, row))

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Pass-through: assumes result is already normalized and cleaned."""
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.get("SIMILARITY_SKOVS", None)

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        # Oracle does not support accurate total_count
        if options.include_total_count:
            logger.warning("`include_total_count=True` is not supported in OracleVectorStore and will be ignored.")

        # Build SQL & bind parameters
        query, bind, _ = await self._inner_search_vector(options, values, vector, **kwargs)

        # Always run streaming search (even if include_total_count=True)
        stream: AsyncIterable[dict[str, Any]] = self._fetch_records(query, bind)

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(stream, options),
            total_count=None,  # always None in Oracle
        )

    async def _inner_search_vector(
        self,
        options: VectorSearchOptions,
        values: Any | None,
        vector: Sequence[float | int] | None,
        **kwargs: Any,
    ) -> tuple[str, list[Any], list[str]]:
        if vector is None:
            vector = await self._generate_vector_from_values(values, options)

        if vector is None or len(vector) == 0:
            raise VectorSearchExecutionException("Vector cannot be None or empty.")

        if options.vector_property_name is None:
            raise VectorStoreOperationException("vector_property_name cannot be None")

        vector_field = next(
            field for field in self.definition.vector_fields if field.name == options.vector_property_name
        )

        dtype = vector_field.type_ if vector_field.type_ else "float32"
        if isinstance(vector, (list)):
            _, code = KIND_MAP[dtype]
            vector = array.array(code, vector)

        table = self._full_table_name()
        # When building filter:
        parsed_filter = self._build_filter(options.filter)
        filter_clause: str | None = None
        filter_binds: list[Any] = []

        if parsed_filter is not None:
            filter_clause = parsed_filter[0]
            filter_binds.extend(parsed_filter[1].values())

        query, bind_values, columns = self._build_search_query(
            table,
            self.definition.key_field,
            self.definition.data_fields,
            self.definition.vector_fields,
            vector,
            vector_field,
            options,
            filter_clause,
        )

        # Append filter binds after vector
        bind_values.extend(filter_binds)
        return query, bind_values, columns

    @override
    def _lambda_parser(self, node: ast.AST, bind_counter: BindCounter | None = None) -> Any:
        """Parse a lambda AST node and return a tuple: (sql_expression, bind_values_dict).

        Uses bind variables for all scalar values, including dates.
        """
        if bind_counter is None:
            bind_counter = BindCounter()

        bind_dict: dict[str, Any] = {}

        match node:
            # Comparisons
            case ast.Compare():
                # IS / IS NOT NULL
                if isinstance(node.ops[0], (ast.Is, ast.IsNot)):
                    left_sql, left_bind = self._lambda_parser(node.left, bind_counter)
                    bind_dict.update(left_bind)
                    right = node.comparators[0]
                    if isinstance(right, ast.Constant) and right.value is None:
                        op_str = "IS" if isinstance(node.ops[0], ast.Is) else "IS NOT"
                        return (f"{left_sql} {op_str} NULL", bind_dict)
                    raise NotImplementedError("IS comparison only supports None/NULL checks")

                # Chained comparisons: a <= b < c
                if len(node.ops) > 1:
                    values = []
                    for idx in range(len(node.ops)):
                        left_node = node.left if idx == 0 else node.comparators[idx - 1]
                        right_node = node.comparators[idx]
                        op = node.ops[idx]
                        expr, binds = self._lambda_parser(
                            ast.Compare(left=left_node, ops=[op], comparators=[right_node]), bind_counter
                        )
                        values.append(expr)
                        bind_dict.update(binds)
                    return (f"({' AND '.join(values)})", bind_dict)

                # Single comparison
                left_sql, left_bind = self._lambda_parser(node.left, bind_counter)
                right_sql, right_bind = self._lambda_parser(node.comparators[0], bind_counter)
                bind_dict.update(left_bind)
                bind_dict.update(right_bind)
                op = node.ops[0]

                if isinstance(op, ast.Eq):
                    return (f"{left_sql} = {right_sql}", bind_dict)
                if isinstance(op, ast.NotEq):
                    return (f"{left_sql} <> {right_sql}", bind_dict)
                if isinstance(op, ast.Gt):
                    return (f"{left_sql} > {right_sql}", bind_dict)
                if isinstance(op, ast.GtE):
                    return (f"{left_sql} >= {right_sql}", bind_dict)
                if isinstance(op, ast.Lt):
                    return (f"{left_sql} < {right_sql}", bind_dict)
                if isinstance(op, ast.LtE):
                    return (f"{left_sql} <= {right_sql}", bind_dict)
                if isinstance(op, ast.In):
                    return (f"{left_sql} IN {right_sql}", bind_dict)
                if isinstance(op, ast.NotIn):
                    return (f"{left_sql} NOT IN {right_sql}", bind_dict)
                raise NotImplementedError(f"Unsupported comparison operator: {type(op)}")

            # Boolean operations
            case ast.BoolOp():
                parts = []
                for v in node.values:
                    sql, binds = self._lambda_parser(v, bind_counter)
                    parts.append(sql)
                    bind_dict.update(binds)
                if isinstance(node.op, ast.And):
                    return (f"({' AND '.join(parts)})", bind_dict)
                if isinstance(node.op, ast.Or):
                    return (f"({' OR '.join(parts)})", bind_dict)
                raise NotImplementedError(f"Unsupported BoolOp: {type(node.op)}")

            # Unary operations
            case ast.UnaryOp():
                if isinstance(node.op, ast.Not):
                    operand_sql, operand_bind = self._lambda_parser(node.operand, bind_counter)
                    bind_dict.update(operand_bind)
                    return (f"NOT ({operand_sql})", bind_dict)
                raise NotImplementedError(f"Unsupported UnaryOp: {type(node.op)}")

            # Handling attribute or name nodes (fields)
            case ast.Attribute():
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(f"Field '{node.attr}' not in data model.")
                return (f'"{node.attr}"', {})
            case ast.Name():
                if node.id not in self.definition.storage_names:
                    raise VectorStoreOperationException(f"Field '{node.id}' not in data model.")
                return (f'"{node.id}"', {})

            # Constants (scalar values) used in this module
            case ast.Constant():
                val = node.value
                if val is None:
                    return ("NULL", {})
                bind_name = bind_counter.next_bind()
                return (f":{bind_name}", {bind_name: val})

            # Lists (for IN operator)
            case ast.List():
                parts = []
                for elt in node.elts:
                    elt_sql, elt_bind = self._lambda_parser(elt, bind_counter)
                    parts.append(elt_sql)
                    bind_dict.update(elt_bind)
                return (f"({', '.join(parts)})", bind_dict)

            # Function calls
            case ast.Call():
                # Supported methods in this block: contains, startswith, endswith, between
                if isinstance(node.func, ast.Attribute):
                    obj_sql, obj_bind = self._lambda_parser(node.func.value, bind_counter)
                    bind_dict.update(obj_bind)
                    sql_args = []
                    for arg in node.args:
                        arg_sql, arg_bind = self._lambda_parser(arg, bind_counter)
                        sql_args.append(arg_sql)
                        bind_dict.update(arg_bind)
                    method = node.func.attr
                    if method == "contains" and len(sql_args) == 1:
                        return (f"LOWER({obj_sql}) LIKE LOWER('%' || {sql_args[0]} || '%')", bind_dict)
                    if method == "startswith" and len(sql_args) == 1:
                        return (f"{obj_sql} LIKE {sql_args[0]} || '%'", bind_dict)
                    if method == "endswith" and len(sql_args) == 1:
                        return (f"{obj_sql} LIKE '%' || {sql_args[0]}", bind_dict)
                    if method == "between" and len(sql_args) == 2:
                        return (f"{obj_sql} BETWEEN {sql_args[0]} AND {sql_args[1]}", bind_dict)

                # Handle datetime function with arguments (year, month, day)
                if isinstance(node.func, ast.Name) and node.func.id == "datetime":
                    if not (3 <= len(node.args) <= 6):
                        raise NotImplementedError("datetime() only supports between 3 and 6 integer arguments")

                    def get_const(arg: ast.AST) -> int:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                            return arg.value
                        raise NotImplementedError("datetime() arguments must be int constants")

                    year = get_const(node.args[0])
                    month = get_const(node.args[1])
                    day = get_const(node.args[2])
                    hour = get_const(node.args[3]) if len(node.args) > 3 else 0
                    minute = get_const(node.args[4]) if len(node.args) > 4 else 0
                    second = get_const(node.args[5]) if len(node.args) > 5 else 0

                    dt = datetime.datetime(year, month, day, hour, minute, second)
                    bind_name = bind_counter.next_bind()
                    bind_dict[bind_name] = dt
                    return (f":{bind_name}", bind_dict)

                # Handle date function with arguments (year, month, day)
                if isinstance(node.func, ast.Name) and node.func.id == "date":
                    if len(node.args) != 3:
                        raise NotImplementedError("date() only supports year, month, day as int constants")

                    def get_const(arg: ast.AST) -> int:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                            return arg.value
                        raise NotImplementedError("date() arguments must be int constants")

                    year = get_const(node.args[0])
                    month = get_const(node.args[1])
                    day = get_const(node.args[2])

                    dt = datetime.date(year, month, day)  # type: ignore[assignment]
                    bind_name = bind_counter.next_bind()
                    bind_dict[bind_name] = dt
                    return (f":{bind_name}", bind_dict)

        raise NotImplementedError(f"Unsupported AST node: {type(node)}")


# region: Oracle Store


@release_candidate
class OracleStore(VectorStore):
    """VectorStore wrapper holding a shared Oracle connection-pool."""

    connection_pool: oracledb.AsyncConnectionPool | None = None
    db_schema: str | None = None
    env_file_path: str | None = None
    env_file_encoding: str | None = None

    def _build_select_table_names_query(self) -> tuple[str, dict[str, str]]:
        if self.db_schema:
            sql = """
                SELECT table_name
                FROM all_tables
                WHERE owner = :schema
                ORDER BY table_name
            """
            bind_vars = {"schema": self.db_schema}
        else:
            sql = """
                SELECT table_name
                FROM user_tables
                ORDER BY table_name
            """
            bind_vars = {}

        return sql, bind_vars

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        collection_name: str | None = None,
        definition: VectorStoreCollectionDefinition | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        pool_args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> OracleCollection:
        """Return an OracleCollection that shares this store's pool.

        Args:
            record_type: The type of the records that will be used.
            collection_name: Name of the table (optional if `definition` supplied).
            definition: VectorStoreCollectionDefinition describing schema/PK.
            embedding_generator: Overrides store's default generator.
            pool_args: Dict of connection-pool overrides (user, min, max, …).
            **kwargs: Additional keyword arguments passed to OracleCollection.

        Returns:
            OracleCollection ready for use (optionally as an async context manager).
        """
        return OracleCollection(
            record_type=record_type,
            collection_name=collection_name,
            db_schema=self.db_schema,
            definition=definition,
            connection_pool=self.connection_pool,
            env_file_path=self.env_file_path,
            env_file_encoding=self.env_file_encoding,
            embedding_generator=embedding_generator or self.embedding_generator,
            pool_args=pool_args,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs: Any) -> Sequence[str]:
        """Get the names of all collections."""
        if self.connection_pool is None:
            raise VectorStoreOperationException("Store has no connection pool.")

        sql, binds = self._build_select_table_names_query()

        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetchall(sql, binds)
            return [row[0] for row in rows]
