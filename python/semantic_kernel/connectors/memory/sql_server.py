# Copyright (c) Microsoft. All rights reserved.

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

from semantic_kernel.data.const import DISTANCE_FUNCTION_DIRECTION_HELPER, DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import AnyTagsEqualTo, EqualTo, KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizedSearchMixin,
    VectorSearchFilter,
    VectorSearchOptions,
    VectorSearchResult,
)
from semantic_kernel.data.vector_storage import VectorStore, VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorStoreOperationException
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental

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

TKey = TypeVar("TKey", str, int)
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
}

__all__ = ["SqlServerCollection", "SqlServerStore"]

# region: Settings


@experimental
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


@experimental
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


@experimental
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


@experimental
class SqlServerCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """SQL collection implementation."""

    connection: Any | None = None
    settings: SqlSettings | None = None
    supported_key_types: ClassVar[list[str] | None] = ["str", "int"]
    supported_vector_types: ClassVar[list[str] | None] = ["float"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        connection_string: str | None = None,
        connection: "Connection | None" = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the collection.

        Args:
            collection_name: The name of the collection, which corresponds to the table name.
            data_model_type: The type of the data model.
            data_model_definition: The data model definition.
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
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            connection=connection,
            settings=settings,
            managed_client=managed_client,
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
        data_fields = [
            field
            for field in self.data_model_definition.fields.values()
            if isinstance(field, VectorStoreRecordDataField)
        ]
        vector_fields = self.data_model_definition.vector_fields
        schema, table = self._get_schema_and_table()
        # Check how many parameters are likely to be passed
        # to the command, if it exceeds the maximum, split the records
        # into smaller chunks
        max_records = SQL_PARAMETER_SAFETY_MAX_COUNT // len(self.data_model_definition.fields)
        batches = []
        for i in range(0, len(records), max_records):
            batches.append(records[i : i + max_records])
        keys = []
        for batch in batches:
            command = _build_merge_query(
                schema, table, self.data_model_definition.key_field, data_fields, vector_fields, batch
            )
            with self.connection.cursor() as cur:
                cur.execute(*command.to_execute())
                while cur.nextset():
                    keys.extend([row[0] for row in cur.fetchall()])
        if not keys:
            raise VectorStoreOperationException("No keys were returned from the merge query.")
        return keys

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[dict[str, Any]] | None:
        """Get records from the database.

        Args:
            keys: The keys to get.
            **kwargs: Additional arguments.

        Returns:
            The records from the store, not deserialized.
        """
        if not keys:
            return None
        query = _build_select_query(
            *self._get_schema_and_table(),
            self.data_model_definition.key_field,
            [
                field
                for field in self.data_model_definition.fields.values()
                if isinstance(field, VectorStoreRecordDataField)
            ],
            self.data_model_definition.vector_fields if kwargs.get("include_vectors", True) else None,
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
            self.data_model_definition.key_field,
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

        data_fields = [
            field
            for field in self.data_model_definition.fields.values()
            if isinstance(field, VectorStoreRecordDataField)
        ]
        create_table_query = _build_create_table_query(
            *self._get_schema_and_table(),
            key_field=self.data_model_definition.key_field,
            data_fields=data_fields,
            vector_fields=self.data_model_definition.vector_fields,
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
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection."""
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        with self.connection.cursor() as cur:
            cur.execute(*_build_delete_table_query(*self._get_schema_and_table()).to_execute())
            logger.debug(f"SqlServer table '{self.collection_name}' deleted successfully.")

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if vector is not None:
            query = _build_search_query(
                *self._get_schema_and_table(),
                self.data_model_definition.key_field,
                [
                    field
                    for field in self.data_model_definition.fields.values()
                    if isinstance(field, VectorStoreRecordDataField)
                ],
                self.data_model_definition.vector_fields,
                vector,
                options,
            )
        elif search_text:
            raise VectorSearchExecutionException("Text search not supported.")
        elif vectorizable_text:
            raise VectorSearchExecutionException("Vectorizable text search not supported.")

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
                        if col in self.data_model_definition.vector_field_names
                        else row.__getattribute__(col)
                    )
                    for col in col_names
                }
                yield record
                await asyncio.sleep(0)

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.pop(SCORE_FIELD_NAME, None)


# region: SQL Server Store


@experimental
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
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the SQL Store.

        Args:
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
                    "Invalid settings provided. Please check the connection string."
                ) from e

        super().__init__(settings=settings, connection=connection, managed_client=managed_client, **kwargs)

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
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        self.vector_record_collections[collection_name] = SqlServerCollection(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            connection=self.connection,
            settings=self.settings,
            **kwargs,
        )
        return self.vector_record_collections[collection_name]


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
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
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
                f'"{key_field.name}" {_python_type_to_sql(key_field.property_type, is_key=True)} NOT NULL,\n'
            )
            # add the data fields
            [
                command.query.append(f'"{field.name}" {_python_type_to_sql(field.property_type)} NULL,\n')
                for field in data_fields
            ]
            # add the vector fields
            for field in vector_fields:
                if field.dimensions is None:
                    raise VectorStoreOperationException(f"Vector dimensions are not defined for field '{field.name}'")
                if field.index_kind is not None and field.index_kind != IndexKind.FLAT:
                    # Only FLAT index kind is supported
                    # None is also accepted, which means no explicit index kind
                    # is set, so implicit default is used
                    raise VectorStoreOperationException(
                        f"Index kind '{field.index_kind}' is not supported for field '{field.name}'"
                    )
                command.query.append(f'"{field.name}" VECTOR({field.dimensions}) NULL,\n')
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
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField] | None,
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
        strings = [f"{table_identifier}.{field.name}" for field in fields]
    else:
        strings = [field.name for field in fields]
    command.query.append_list(strings)


def _build_merge_query(
    schema: str,
    table: str,
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
    records: Sequence[dict[str, Any]],
) -> SqlCommand:
    """Build the MERGE TABLE query based on the data model."""
    command = SqlCommand()
    # Declare a temp table to store the keys that are updated
    command.query.append(
        "DECLARE @UpsertedKeys TABLE (KeyColumn "
        f"{_python_type_to_sql(key_field.property_type or 'str', is_key=True)});\n"
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
                    value = record.get(field.name)
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
        command.query.append(f"t.{key_field.name} = s.{key_field.name}")
    # Set the Matched clause
    command.query.append("WHEN MATCHED THEN\n")
    command.query.append("UPDATE SET ")
    command.query.append_list(
        [f"t.{field.name} = s.{field.name}" for field in chain(data_fields, vector_fields)], suffix="\n"
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
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField] | None,
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
        command.query.append(f"WHERE {key_field.name} IN\n")
        with command.query.in_parenthesis():
            # add the keys
            command.query.append_list(["?"] * len(keys))
            command.add_parameters([_cast_value(key) for key in keys])
    command.query.append(";")
    return command


def _build_delete_query(
    schema: str,
    table: str,
    key_field: VectorStoreRecordKeyField,
    keys: Sequence[Any],
) -> SqlCommand:
    """Build the DELETE query based on the data model."""
    command = SqlCommand("DELETE FROM")
    # start the DELETE statement
    command.query.append_table_name(schema, table)
    # add the WHERE clause
    command.query.append(f"WHERE [{key_field.name}] IN")
    with command.query.in_parenthesis():
        # add the keys
        command.query.append_list(["?"] * len(keys))
        command.add_parameters([_cast_value(key) for key in keys])
    command.query.append(";")
    return command


def _build_filter(command: SqlCommand, filters: VectorSearchFilter):
    """Build the filter query based on the data model."""
    if not filters.filters:
        return
    command.query.append("WHERE ")
    for filter in filters.filters:
        match filter:
            case EqualTo():
                command.query.append(f"[{filter.field_name}] = ? AND\n")
                command.add_parameter(_cast_value(filter.value))
            case AnyTagsEqualTo():
                command.query.append(f"? IN [{filter.field_name}] AND\n")
                command.add_parameter(_cast_value(filter.value))
    # remove the last AND
    command.query.remove_last(4)
    command.query.append("\n")


def _build_search_query(
    schema: str,
    table: str,
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
    vector: list[float],
    options: VectorSearchOptions,
) -> SqlCommand:
    """Build the SELECT query based on the data model."""
    # start the SELECT statement
    command = SqlCommand("SELECT ")
    # add the data and vector fields
    _add_field_names(command, key_field, data_fields, vector_fields if options.include_vectors else None)
    # add the vector search clause
    vector_field: VectorStoreRecordVectorField | None = None
    if options.vector_field_name:
        vector_field = next(
            (field for field in vector_fields if field.name == options.vector_field_name),
            None,
        )
    elif len(vector_fields) == 1:
        vector_field = vector_fields[0]
    if not vector_field:
        raise VectorStoreOperationException("Vector field not specified.")

    asc: bool = True
    if vector_field.distance_function:
        distance_function = DISTANCE_FUNCTION_MAP.get(vector_field.distance_function)
        if not distance_function:
            raise VectorStoreOperationException(f"Distance function '{vector_field.distance_function}' not supported.")
        asc = DISTANCE_FUNCTION_DIRECTION_HELPER[vector_field.distance_function](0, 1)
    else:
        distance_function = "cosine"

    command.query.append(
        f", VECTOR_DISTANCE('{distance_function}', {vector_field.name}, CAST(? AS VECTOR({vector_field.dimensions}))) as {SCORE_FIELD_NAME}\n",  # noqa: E501
    )
    command.add_parameter(_cast_value(vector))
    # add the FROM clause
    command.query.append_table_name(schema, table, prefix=" FROM", newline=True)
    # add the WHERE clause
    _build_filter(command, options.filter)
    # add the ORDER BY clause
    command.query.append(f"ORDER BY {SCORE_FIELD_NAME} {'ASC' if asc else 'DESC'}\n")
    command.query.append(f"OFFSET {options.skip} ROWS FETCH NEXT {options.top} ROWS ONLY;")
    return command
