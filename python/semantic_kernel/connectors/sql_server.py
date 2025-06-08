# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
import json
import logging
import re
import struct
import sys
from collections.abc import AsyncIterable, Sequence
from contextlib import contextmanager
from io import StringIO
from itertools import chain
from typing import TYPE_CHECKING, Any, ClassVar, Final, Generic, TypeVar

from azure.identity.aio import DefaultAzureCredential
from pydantic import SecretStr, ValidationError, field_validator

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DISTANCE_FUNCTION_DIRECTION_HELPER,
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
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

if TYPE_CHECKING:
    from pyodbc import Connection


logger = logging.getLogger(__name__)

TKey = TypeVar("TKey", bound=str | int)
TModel = TypeVar("TModel")

# maximum number of parameters for SQL Server
# The actual limit is 2100, but we leave some space
SQL_PARAMETER_SAFETY_MAX_COUNT: Final[int] = 2000
SQL_PARAMETER_MAX_COUNT: Final[int] = 2100
SCORE_FIELD_NAME: Final[str] = "_vector_distance_value"
DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_DISTANCE: "cosine",
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.DOT_PROD: "dot",
    DistanceFunction.DEFAULT: "cosine",
}
INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {
    IndexKind.FLAT: "flat",
    IndexKind.DEFAULT: "flat",
}

__all__ = ["SqlServerCollection", "SqlServerStore"]

# region: Settings


@release_candidate
class SqlSettings(KernelBaseSettings):
    """SQL settings.

    The settings are first loaded from environment variables with
    the prefix 'SQL_SERVER_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'SQL_SERVER_':
    - connection_string: str - The connection string of the SQL Server, including for Azure SQL.
        For SQL Server: the connection string should include the server name, database name, user ID, and password.
        For example: "Driver={ODBC Driver 18 for SQL Server};Server=server_name;Database=database_name;UID=user_id;PWD=password;"
        For Azure SQL: This value can be found in the Keys & Endpoint section when examining
        your resource from the Azure portal.
        The advice is to use a password-less setup, see
        https://learn.microsoft.com/en-us/azure/azure-sql/database/azure-sql-passwordless-migration-python?view=azuresql&preserve-view=true&tabs=sign-in-azure-cli%2Cazure-portal-create%2Cazure-portal-assign%2Capp-service-identity#update-the-local-connection-configuration for more info.
        (Env var name: SQL_SERVER_CONNECTION_STRING)
    """  # noqa: E501

    env_prefix: ClassVar[str] = "SQL_SERVER_"

    connection_string: SecretStr

    @field_validator("connection_string", mode="before")
    @classmethod
    def validate_connection_string(cls, value: str) -> str:
        """Validate the connection string.

        The LongAsMax=yes option is added to the connection string if it is not present.
        This is needed to supply vectors as query parameters.

        """
        if "LongAsMax=yes" not in value:
            if value.endswith(";"):
                value = value[:-1]
            return f"{value};LongAsMax=yes;"
        return value


# region: SQL Command and Query Builder


@release_candidate
class QueryBuilder:
    """A class that helps you build strings for SQL queries."""

    def __init__(self, initial_string: "QueryBuilder | str | None" = None):
        """Initialize the StringBuilder with an empty StringIO object."""
        self._file_str = StringIO()
        if initial_string:
            self._file_str.write(str(initial_string))

    def append(self, string: str, suffix: str | None = None):
        """Append a string to the StringBuilder."""
        self._file_str.write(string)
        if suffix:
            self._file_str.write(suffix)

    def append_list(self, strings: Sequence[str], sep: str = ", ", suffix: str | None = None):
        """Append a list of strings to the StringBuilder.

        Optionally set the separator (default: `, `) and a suffix (default is None).
        """
        if not strings:
            return
        for string in strings[:-1]:
            self.append(string, suffix=sep)
        self.append(strings[-1], suffix=suffix)

    def append_table_name(
        self, schema: str, table_name: str, prefix: str = "", suffix: str | None = None, newline: bool = False
    ) -> None:
        """Append a table name to the StringBuilder with schema.

        This includes square brackets around the schema and table name.
        And spaces around the table name.

        Args:
            schema: The schema name.
            table_name: The table name.
            prefix: Optional prefix to add before the table name.
            suffix: Optional suffix to add after the table name.
            newline: Whether to add a newline after the table name or suffix.
        """
        self.append(f"{prefix} [{schema}].[{table_name}] {suffix or ''}", suffix="\n" if newline else "")

    def remove_last(self, number_of_chars: int):
        """Remove the last number_of_chars from the StringBuilder."""
        current_pos = self._file_str.tell()
        if current_pos >= number_of_chars:
            self._file_str.seek(current_pos - number_of_chars)
            self._file_str.truncate()

    @contextmanager
    def in_parenthesis(self, prefix: str | None = None, suffix: str | None = None):
        """Context manager to add parentheses around a block of strings.

        Args:
            prefix: Optional prefix to add before the opening parenthesis.
            suffix: Optional suffix to add after the closing parenthesis.

        """
        self.append(f"{prefix or ''} (")
        yield
        self.append(f") {suffix or ''}")

    @contextmanager
    def in_logical_group(self):
        """Create a logical group with BEGIN and END."""
        self.append("BEGIN", suffix="\n")
        yield
        self.append("\nEND", suffix="\n")

    def __str__(self):
        """Return the string representation of the StringBuilder."""
        return self._file_str.getvalue()


@release_candidate
class SqlCommand:
    """A class that represents a SQL command with parameters."""

    def __init__(
        self,
        query: QueryBuilder | str | None = None,
    ):
        """Initialize the SqlCommand.

        This only allows for creation of the query string, use the add_parameter
        and add_parameters methods to add parameters to the command.

        Args:
            query: The SQL command string or QueryBuilder object.

        """
        self.query = QueryBuilder(query)
        self.parameters: list[str] = []

    def add_parameter(self, value: str) -> None:
        """Add a parameter to the SqlCommand."""
        if (len(self.parameters) + 1) > SQL_PARAMETER_MAX_COUNT:
            raise VectorStoreOperationException("The maximum number of parameters is 2100.")
        self.parameters.append(value)

    def add_parameters(self, values: Sequence[str] | tuple[str, ...]) -> None:
        """Add multiple parameters to the SqlCommand."""
        if (len(self.parameters) + len(values)) > SQL_PARAMETER_MAX_COUNT:
            raise VectorStoreOperationException(f"The maximum number of parameters is {SQL_PARAMETER_MAX_COUNT}.")
        self.parameters.extend(values)

    def __str__(self):
        """Return the string representation of the SqlCommand."""
        if self.parameters:
            logger.debug("This command has parameters.")
        return str(self.query)

    def to_execute(self) -> tuple[str, tuple[str, ...]]:
        """Return the command and parameters for execute."""
        return str(self.query), tuple(self.parameters)


async def _get_mssql_connection(settings: SqlSettings) -> "Connection":
    """Get a connection to the SQL Server database, optionally with Entra Auth."""
    from pyodbc import connect

    mssql_connection_string = settings.connection_string.get_secret_value()
    if any(s in mssql_connection_string.lower() for s in ["uid"]):
        attrs_before: dict | None = None
    else:
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            # Get the access token
            token_bytes = (await credential.get_token("https://database.windows.net/.default")).token.encode(
                "UTF-16-LE"
            )
            token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
            SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
            attrs_before = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}

    return connect(mssql_connection_string, attrs_before=attrs_before)


# region: SQL Server Collection


@release_candidate
class SqlServerCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """SQL collection implementation."""

    connection: Any | None = None
    settings: SqlSettings | None = None
    supported_key_types: ClassVar[set[str] | None] = {"str", "int"}
    supported_vector_types: ClassVar[set[str] | None] = {"float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        connection_string: str | None = None,
        connection: "Connection | None" = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the collection.

        Args:
            record_type: The type of the data model.
            definition: The data model definition.
            collection_name: The name of the collection, which corresponds to the table name.
            embedding_generator: The embedding generator to use.
            connection_string: The connection string to the database.
            connection: The connection, make sure to set the `LongAsMax=yes` option on the construction string used.
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            **kwargs: Additional arguments.
        """
        managed_client = not connection
        settings = None
        if not connection:
            try:
                settings = SqlSettings(
                    connection_string=connection_string,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise VectorStoreInitializationException(
                    "Invalid settings provided. Please check the connection string and database name."
                ) from e

        super().__init__(
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            connection=connection,
            settings=settings,
            managed_client=managed_client,
            embedding_generator=embedding_generator,
        )

    @override
    async def __aenter__(self) -> Self:
        # If the connection pool was not provided, create a new one.
        if not self.connection:
            if not self.settings:  # pragma: no cover
                # this should never happen, but just in case
                raise VectorStoreInitializationException("No connection or settings provided.")
            self.connection = await _get_mssql_connection(self.settings)
        self.connection.__enter__()
        return self

    @override
    async def __aexit__(self, *args):
        # Only close the connection if it was created by the collection.
        if self.managed_client and self.connection:
            self.connection.close()
            self.connection = None

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
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")
        if not records:
            return []
        data_fields = self.definition.data_fields
        vector_fields = self.definition.vector_fields
        schema, table = self._get_schema_and_table()
        # Check how many parameters are likely to be passed
        # to the command, if it exceeds the maximum, split the records
        # into smaller chunks
        max_records = SQL_PARAMETER_SAFETY_MAX_COUNT // len(self.definition.fields)
        batches = []
        for i in range(0, len(records), max_records):
            batches.append(records[i : i + max_records])
        keys = []
        for batch in batches:
            command = _build_merge_query(schema, table, self.definition.key_field, data_fields, vector_fields, batch)
            with self.connection.cursor() as cur:
                cur.execute(*command.to_execute())
                while cur.nextset():
                    keys.extend([row[0] for row in cur.fetchall()])
        if not keys:
            raise VectorStoreOperationException("No keys were returned from the merge query.")
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
        query = _build_select_query(
            *self._get_schema_and_table(),
            self.definition.key_field,
            self.definition.data_fields,
            self.definition.vector_fields if kwargs.get("include_vectors", True) else None,
            keys,
        )
        records = [record async for record in self._fetch_records(query)]
        return records if records else None

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records with the given keys.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.
        """
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        if not keys:
            return
        query = _build_delete_query(
            *self._get_schema_and_table(),
            self.definition.key_field,
            keys,
        )
        with self.connection.cursor() as cur:
            cur.execute(*query.to_execute())

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
    async def create_collection(
        self, *, create_if_not_exists: bool = True, queries: list[str] | None = None, **kwargs: Any
    ) -> None:
        """Create a SQL table based on the data model.

        Alternatively, you can pass a list of queries to execute.
        If supplied, only the queries will be executed.

        Args:
            create_if_not_exists: Whether to create the table if it does not exist, default is True.
                This means, that by default the table will only be created if it does not exist.
                So if there is a existing table with the same name, it will not be created or modified.
            queries: A list of SQL queries to execute.
            **kwargs: Additional arguments.

        """
        if self.connection is None:
            raise VectorStoreOperationException("Connection is not available, use the collection as a context manager.")

        if queries:
            with self.connection.cursor() as cursor:
                for query in queries:
                    cursor.execute(query)
            return

        create_table_query = _build_create_table_query(
            *self._get_schema_and_table(),
            key_field=self.definition.key_field,
            data_fields=self.definition.data_fields,
            vector_fields=self.definition.vector_fields,
            if_not_exists=create_if_not_exists,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(*create_table_query.to_execute())
        logger.info(f"SqlServer table '{self.collection_name}' created successfully.")

    def _get_schema_and_table(self) -> tuple[str, str]:
        """Get the schema and table name from the collection name."""
        if "." in self.collection_name:
            schema, table = self.collection_name.split(".", maxsplit=1)
        else:
            schema = "dbo"
            table = self.collection_name
        return schema, table

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        with self.connection.cursor() as cursor:
            cursor.execute(*_build_select_table_name_query(*self._get_schema_and_table()).to_execute())
            row = cursor.fetchone()
            return bool(row)

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Delete the collection."""
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        with self.connection.cursor() as cur:
            cur.execute(*_build_delete_table_query(*self._get_schema_and_table()).to_execute())
            logger.debug(f"SqlServer table '{self.collection_name}' deleted successfully.")

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if vector is None:
            vector = await self._generate_vector_from_values(values, options)
        if not vector:
            raise VectorSearchExecutionException("No vector provided.")
        query = _build_search_query(
            *self._get_schema_and_table(),
            self.definition.key_field,
            self.definition.data_fields,
            self.definition.vector_fields,
            vector,
            options,
            self._build_filter(options.filter),  # type: ignore
        )

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(self._fetch_records(query), options),
            total_count=None,
        )

    async def _fetch_records(self, query: SqlCommand) -> AsyncIterable[dict[str, Any]]:
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")
        with self.connection.cursor() as cur:
            cur.execute(*query.to_execute())
            col_names = [desc[0] for desc in cur.description]
            for row in cur:
                record = {
                    col: (
                        json.loads(row.__getattribute__(col))
                        if col in self.definition.vector_field_names
                        else row.__getattribute__(col)
                    )
                    for col in col_names
                }
                yield record
                await asyncio.sleep(0)

    @override
    def _lambda_parser(self, node: ast.AST) -> "SqlCommand":  # type: ignore
        """Parse a Python lambda AST node and return a SqlCommand object."""
        command = SqlCommand()

        def parse(node: ast.AST) -> str:
            match node:
                case ast.Compare():
                    if len(node.ops) > 1:
                        # Chain comparisons (e.g., 1 < x < 3) become AND of each comparison
                        values = []
                        for idx in range(len(node.ops)):
                            left = node.left if idx == 0 else node.comparators[idx - 1]
                            right = node.comparators[idx]
                            op = node.ops[idx]
                            values.append(parse(ast.Compare(left=left, ops=[op], comparators=[right])))
                        return f"({' AND '.join(values)})"
                    left = parse(node.left)  # type: ignore
                    right_node = node.comparators[0]
                    op = node.ops[0]
                    match op:
                        case ast.In():
                            right = parse(right_node)  # type: ignore
                            return f"{left} IN {right}"
                        case ast.NotIn():
                            right = parse(right_node)  # type: ignore
                            return f"{left} NOT IN {right}"
                        case ast.Eq():
                            right = parse(right_node)  # type: ignore
                            return f"{left} = {right}"
                        case ast.NotEq():
                            right = parse(right_node)  # type: ignore
                            return f"{left} <> {right}"
                        case ast.Gt():
                            right = parse(right_node)  # type: ignore
                            return f"{left} > {right}"
                        case ast.GtE():
                            right = parse(right_node)  # type: ignore
                            return f"{left} >= {right}"
                        case ast.Lt():
                            right = parse(right_node)  # type: ignore
                            return f"{left} < {right}"
                        case ast.LtE():
                            right = parse(right_node)  # type: ignore
                            return f"{left} <= {right}"
                    raise NotImplementedError(f"Unsupported operator: {type(op)}")
                case ast.BoolOp():
                    op = node.op  # type: ignore
                    values = [parse(v) for v in node.values]
                    if isinstance(op, ast.And):
                        return f"({' AND '.join(values)})"
                    if isinstance(op, ast.Or):
                        return f"({' OR '.join(values)})"
                    raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
                case ast.UnaryOp():
                    match node.op:
                        case ast.Not():
                            operand = parse(node.operand)
                            return f"NOT ({operand})"
                        case ast.UAdd() | ast.USub() | ast.Invert():
                            raise NotImplementedError("Unary +, -, ~ are not supported in SQL filters.")
                case ast.Attribute():
                    # Only allow attributes that are in the data model
                    if node.attr not in self.definition.storage_names:
                        raise VectorStoreOperationException(
                            f"Field '{node.attr}' not in data model (storage property names are used)."
                        )
                    return f"[{node.attr}]"
                case ast.Name():
                    # Only allow names that are in the data model
                    if node.id not in self.definition.storage_names:
                        raise VectorStoreOperationException(
                            f"Field '{node.id}' not in data model (storage property names are used)."
                        )
                    return f"[{node.id}]"
                case ast.Constant():
                    # Always use parameterization for constants
                    command.add_parameter(node.value)
                    return "?"
                case ast.List():
                    # For IN/NOT IN lists, parameterize each element
                    placeholders = []
                    for elt in node.elts:
                        placeholders.append(parse(elt))
                    return f"({', '.join(placeholders)})"
            raise NotImplementedError(f"Unsupported AST node: {type(node)}")

        where_clause = parse(node)
        command.query.append(where_clause)
        return command

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.pop(SCORE_FIELD_NAME, None)


# region: SQL Server Store


@release_candidate
class SqlServerStore(VectorStore):
    """SQL Store implementation.

    This class is used to store and retrieve data from an SQL database.
    It uses the SqlServerCollection class to perform the actual operations.
    """

    connection: Any | None = None
    settings: SqlSettings | None = None

    def __init__(
        self,
        connection_string: str | None = None,
        connection: "Connection | None" = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the SQL Store.

        Args:
            connection_string: The connection string to the database.
            connection: The connection, make sure to set the `LongAsMax=yes` option on the construction string used.
            embedding_generator: The embedding generator to use.
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            **kwargs: Additional arguments.

        """
        if not connection:
            try:
                settings = SqlSettings(
                    connection_string=connection_string,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise VectorStoreInitializationException(
                    "Invalid settings provided. Please check the connection string."
                ) from e
        else:
            settings = None
        super().__init__(
            connection=connection,
            settings=settings,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    @override
    async def __aenter__(self) -> Self:
        # If the connection was not provided, create a new one.
        if not self.connection:
            if not self.settings:  # pragma: no cover
                # this should never happen, but just in case
                raise VectorStoreInitializationException("Settings must be provided to establish a connection.")
            self.connection = await _get_mssql_connection(self.settings)
        self.connection.__enter__()
        return self

    @override
    async def __aexit__(self, *args):
        # Only close the connection if it was created by the store.
        if self.managed_client and self.connection:
            self.connection.close()
        self.connection = None

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        """List the collection names in the database.

        Args:
            **kwargs: Additional arguments.

        Returns:
            A list of collection names.
        """
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the store as a context manager.")
        with self.connection.cursor() as cur:
            cur.execute(*_build_select_table_names_query(schema=kwargs.get("schema")).to_execute())
            rows = cur.fetchall()
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
    ) -> SqlServerCollection:
        return SqlServerCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            connection=self.connection,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )


# region: Query Build Functions


def _python_type_to_sql(python_type_str: str | None, is_key: bool = False) -> str | None:
    """Convert a string representation of a Python type to a SQL data type.

    Args:
        python_type_str: The string representation of the Python type (e.g., "int", "List[str]").
        is_key: Whether the type is a key field.

    Returns:
        Corresponding SQL data type as a string, if found. If the type is not found, return None.
    """
    if python_type_str is None:
        raise VectorStoreOperationException("property type cannot be None")
    # Basic type mapping from Python types (in string form) to SQL types
    type_mapping = {
        "str": "nvarchar(max)" if not is_key else "nvarchar(255)",
        "int": "int",
        "float": "float",
        "bool": "bit",
        "dict": "json",
        "datetime": "datetime2",
        "bytes": "binary",
    }

    # Regular expression to detect lists, e.g., "List[str]" or "List[int]"
    list_pattern = re.compile(r"(?i)List\[(.*)\]")

    # Check if the type is a list
    match = list_pattern.match(python_type_str)
    if match:
        # Extract the inner type of the list and convert it to a SQL array type
        element_type_str = match.group(1)
        sql_element_type = _python_type_to_sql(element_type_str)
        return f"{sql_element_type}[]"

    # Handle basic types
    if python_type_str in type_mapping:
        return type_mapping[python_type_str]

    return None


def _cast_value(value: Any) -> str:
    """Add a cast check to the value."""
    if value is None:
        return "NULL"
    match value:
        case str():
            return value
        case bool():
            return "1" if value else "0"
        case int() | float():
            return f"{value!s}"
        case list() | dict():
            return f"{json.dumps(value)}"
        case bytes():
            return f"CONVERT(VARBINARY(MAX), '{value.hex()}')"
        case _:
            raise VectorStoreOperationException(f"Unsupported type: {type(value)}")


def _add_cast_check(placeholder: str, value: Any) -> str:
    """Add a cast check to the value."""
    if isinstance(value, bytes):
        return f"CONVERT(VARBINARY(MAX), {placeholder})"
    return placeholder


def _build_create_table_query(
    schema: str,
    table: str,
    key_field: VectorStoreField,
    data_fields: list[VectorStoreField],
    vector_fields: list[VectorStoreField],
    if_not_exists: bool = False,
) -> SqlCommand:
    """Build the CREATE TABLE query based on the data model."""
    command = SqlCommand()
    if if_not_exists:
        command.query.append_table_name(
            schema, table, prefix="IF OBJECT_ID(N'", suffix="', N'U') IS NULL", newline=True
        )
    with command.query.in_logical_group():
        command.query.append_table_name(schema, table, prefix="CREATE TABLE", newline=True)
        with command.query.in_parenthesis(suffix=";"):
            # add the key field
            command.query.append(
                f'"{key_field.storage_name or key_field.name}" '
                f"{_python_type_to_sql(key_field.type_, is_key=True)} NOT NULL,\n"
            )
            # add the data fields
            [
                command.query.append(f'"{field.storage_name or field.name}" {_python_type_to_sql(field.type_)} NULL,\n')
                for field in data_fields
            ]
            # add the vector fields
            for field in vector_fields:
                if field.index_kind not in INDEX_KIND_MAP:
                    raise VectorStoreOperationException(
                        f"Index kind '{field.index_kind}' is not supported for field '{field.name}'"
                    )
                command.query.append(f'"{field.storage_name or field.name}" VECTOR({field.dimensions}) NULL,\n')
            # set the primary key
            with command.query.in_parenthesis("PRIMARY KEY", "\n"):
                command.query.append(key_field.name)
    return command


def _build_delete_table_query(
    schema: str,
    table: str,
) -> SqlCommand:
    """Build the DELETE TABLE query based on the data model."""
    command = SqlCommand("DROP TABLE IF EXISTS")
    command.query.append_table_name(schema, table, suffix=";")
    return command


def _build_select_table_names_query(
    schema: str | None = None,
) -> SqlCommand:
    """Build the SELECT TABLE NAMES query based on the data model."""
    command = SqlCommand()
    if schema:
        command.query.append(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE' "
            "AND (@schema is NULL or TABLE_SCHEMA = ?);"
        )
        command.add_parameter(schema)
    else:
        command.query.append("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';")
    return command


def _build_select_table_name_query(
    schema: str,
    table: str,
) -> SqlCommand:
    """Build the SELECT TABLE NAMES query based on the data model."""
    command = SqlCommand(
        "SELECT TABLE_NAME"
        " FROM INFORMATION_SCHEMA.TABLES"
        " WHERE TABLE_TYPE = 'BASE TABLE'"
        " AND (@schema is NULL or TABLE_SCHEMA = ?)"
        " AND TABLE_NAME = ?"
    )
    command.add_parameter(schema)
    command.add_parameter(table)
    return command


def _add_field_names(
    command: SqlCommand,
    key_field: VectorStoreField,
    data_fields: list[VectorStoreField],
    vector_fields: list[VectorStoreField] | None,
    table_identifier: str | None = None,
) -> None:
    """Add the field names to the query builder.

    Args:
        command: The SqlCommand object to add the field names to.
        key_field: The key field.
        data_fields: The data fields.
        vector_fields: The vector fields.
        table_identifier: The table identifier to prefix the field names with, if not given,
            the field name is used as is.
            If passed, then it is used with a dot separating the table name and field name.

    """
    fields = chain([key_field], data_fields, vector_fields or [])
    if table_identifier:
        strings = [f"{table_identifier}.{field.storage_name or field.name}" for field in fields]
    else:
        strings = [field.storage_name or field.name for field in fields]
    command.query.append_list(strings)


def _build_merge_query(
    schema: str,
    table: str,
    key_field: VectorStoreField,
    data_fields: list[VectorStoreField],
    vector_fields: list[VectorStoreField],
    records: Sequence[dict[str, Any]],
) -> SqlCommand:
    """Build the MERGE TABLE query based on the data model."""
    command = SqlCommand()
    # Declare a temp table to store the keys that are updated
    command.query.append(
        f"DECLARE @UpsertedKeys TABLE (KeyColumn {_python_type_to_sql(key_field.type_ or 'str', is_key=True)});\n"
    )
    # start the MERGE statement
    command.query.append_table_name(schema, table, prefix="MERGE INTO", suffix="AS t", newline=True)
    # add the USING  VALUES clause
    with command.query.in_parenthesis(prefix="USING"):
        command.query.append(" VALUES ")
        for record in records:
            with command.query.in_parenthesis(suffix=",\n"):
                query_list = []
                param_list = []
                for field in chain([key_field], data_fields, vector_fields):
                    value = record.get(field.storage_name or field.name)
                    # add the field name to the query list
                    query_list.append(_add_cast_check("?", value))
                    # add the field value to the parameter list
                    param_list.append(_cast_value(value))
                command.query.append_list(query_list)
                command.add_parameters(param_list)
        command.query.remove_last(2)  # remove the last comma and newline
    # with the table column names
    with command.query.in_parenthesis("AS s", " "):
        _add_field_names(command, key_field, data_fields, vector_fields)
    # add the ON clause
    with command.query.in_parenthesis("ON", "\n"):
        command.query.append(
            f"t.{key_field.storage_name or key_field.name} = s.{key_field.storage_name or key_field.name}"
        )
    # Set the Matched clause
    command.query.append("WHEN MATCHED THEN\n")
    command.query.append("UPDATE SET ")
    command.query.append_list(
        [
            f"t.{field.storage_name or field.name} = s.{field.storage_name or field.name}"
            for field in chain(data_fields, vector_fields)
        ],
        suffix="\n",
    )
    # Set the Not Matched clause
    command.query.append("WHEN NOT MATCHED THEN\n")
    with command.query.in_parenthesis("INSERT", " "):
        _add_field_names(command, key_field, data_fields, vector_fields)
    # add the closing parenthesis
    with command.query.in_parenthesis("VALUES", " \n"):
        _add_field_names(command, key_field, data_fields, vector_fields, table_identifier="s")
    # add the closing parenthesis
    command.query.append(f"OUTPUT inserted.{key_field.name} INTO @UpsertedKeys (KeyColumn);\n")
    command.query.append("SELECT KeyColumn FROM @UpsertedKeys;\n")
    return command


def _build_select_query(
    schema: str,
    table: str,
    key_field: VectorStoreField,
    data_fields: list[VectorStoreField],
    vector_fields: list[VectorStoreField] | None,
    keys: Sequence[Any],
) -> SqlCommand:
    """Build the SELECT query based on the data model."""
    command = SqlCommand()
    # start the SELECT statement
    command.query.append("SELECT\n")
    # add the data and vector fields
    _add_field_names(command, key_field, data_fields, vector_fields)
    # add the FROM clause
    command.query.append_table_name(schema, table, prefix=" FROM", newline=True)
    # add the WHERE clause
    if keys:
        command.query.append(f"WHERE {key_field.storage_name or key_field.name} IN\n")
        with command.query.in_parenthesis():
            # add the keys
            command.query.append_list(["?"] * len(keys))
            command.add_parameters([_cast_value(key) for key in keys])
    command.query.append(";")
    return command


def _build_delete_query(
    schema: str,
    table: str,
    key_field: VectorStoreField,
    keys: Sequence[Any],
) -> SqlCommand:
    """Build the DELETE query based on the data model."""
    command = SqlCommand("DELETE FROM")
    # start the DELETE statement
    command.query.append_table_name(schema, table)
    # add the WHERE clause
    command.query.append(f"WHERE [{key_field.storage_name or key_field.name}] IN")
    with command.query.in_parenthesis():
        # add the keys
        command.query.append_list(["?"] * len(keys))
        command.add_parameters([_cast_value(key) for key in keys])
    command.query.append(";")
    return command


def _build_search_query(
    schema: str,
    table: str,
    key_field: VectorStoreField,
    data_fields: list[VectorStoreField],
    vector_fields: list[VectorStoreField],
    vector: Sequence[float | int],
    options: VectorSearchOptions,
    filter: SqlCommand | list[SqlCommand] | None = None,
) -> SqlCommand:
    """Build the SELECT query based on the data model."""
    # start the SELECT statement
    command = SqlCommand("SELECT ")
    # add the data and vector fields
    _add_field_names(command, key_field, data_fields, vector_fields if options.include_vectors else None)
    # add the vector search clause
    vector_field: VectorStoreField | None = None
    if options.vector_property_name:
        vector_field = next(
            (
                field
                for field in vector_fields
                if field.name == options.vector_property_name or field.storage_name == options.vector_property_name
            ),
            None,
        )
    elif len(vector_fields) == 1:
        vector_field = vector_fields[0]
    if not vector_field:
        raise VectorStoreOperationException("Vector field not specified.")
    if vector_field.distance_function not in DISTANCE_FUNCTION_MAP:
        raise VectorStoreOperationException(
            f"Distance function '{vector_field.distance_function}' is not supported for field '{vector_field.name}'"
        )
    distance_function = DISTANCE_FUNCTION_MAP[vector_field.distance_function]
    asc: bool = True
    asc = DISTANCE_FUNCTION_DIRECTION_HELPER[vector_field.distance_function](0, 1)

    command.query.append(
        f", VECTOR_DISTANCE('{distance_function}', {vector_field.storage_name or vector_field.name}, CAST(? AS VECTOR({vector_field.dimensions}))) as {SCORE_FIELD_NAME}\n",  # noqa: E501
    )
    command.add_parameter(_cast_value(vector))
    # add the FROM clause
    command.query.append_table_name(schema, table, prefix=" FROM", newline=True)
    # add the WHERE clause
    if filter:
        if not isinstance(filter, list):
            filter = [filter]
        for idx, f in enumerate(filter):
            if idx == 0:
                command.query.append(" WHERE ")
            else:
                command.query.append(" AND ")
            command.query.append(str(f.query), suffix=" \n")
            command.add_parameters(f.parameters)

    # add the ORDER BY clause
    command.query.append(f"ORDER BY {SCORE_FIELD_NAME} {'ASC' if asc else 'DESC'}\n")
    command.query.append(f"OFFSET {options.skip} ROWS FETCH NEXT {options.top} ROWS ONLY;")
    return command
