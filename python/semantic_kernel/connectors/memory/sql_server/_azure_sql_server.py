# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import re
import struct
import sys
from collections.abc import AsyncIterable, Sequence
from itertools import chain
from typing import Any, ClassVar, Final, Generic, TypeVar

import pyodbc
from azure.identity.aio import DefaultAzureCredential
from pydantic import SecretStr, ValidationError, field_validator
from pyodbc import Row

from semantic_kernel.connectors.memory import logger
from semantic_kernel.connectors.memory.sql_server.sql_command_builder import SqlCommand, StringBuilder
from semantic_kernel.data.const import DISTANCE_FUNCTION_DIRECTION_HELPER, DistanceFunction
from semantic_kernel.data.filter_clauses.any_tags_equal_to_filter_clause import AnyTagsEqualTo
from semantic_kernel.data.filter_clauses.equal_to_filter_clause import EqualTo
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_filter import VectorSearchFilter
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
from semantic_kernel.exceptions import VectorStoreOperationException
from semantic_kernel.exceptions.vector_store_exceptions import VectorSearchExecutionException
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

TKey = TypeVar("TKey", str, int)
TModel = TypeVar("TModel")


SCORE_FIELD_NAME: Final[str] = "_vector_distance_value"
DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_DISTANCE: "cosine",
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.DOT_PROD: "dot",
}


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
        with command.query.in_parenthesis(start="\n", end=";"):
            # add the key field
            command.query.append_with_newline(
                f'"{key_field.name}" {_python_type_to_sql(key_field.property_type, is_key=True)} NOT NULL,'
            )
            # add the data fields
            [
                command.query.append_with_newline(f'"{field.name}" {_python_type_to_sql(field.property_type)} NULL,')
                for field in data_fields
            ]
            # add the vector fields
            for field in vector_fields:
                if field.dimensions is None:
                    raise ValueError(f"Vector dimensions are not defined for field '{field.name}'")
                command.query.append_with_newline(f'"{field.name}" VECTOR({field.dimensions}) NULL,')
            # set the primary key
            with command.query.in_parenthesis("PRIMARY KEY", "\n"):
                command.query.append(key_field.name)
    return command


def _build_delete_table_query(
    schema: str,
    table: str,
) -> SqlCommand:
    """Build the DELETE TABLE query based on the data model."""
    command = SqlCommand()
    command.query.append_table_name(schema, table, prefix="DROP TABLE IF EXISTS", suffix=";")
    return command


def _build_select_table_query(
    schema: str,
    table: str,
) -> SqlCommand:
    """Build the SELECT TABLE query based on the data model."""
    command = SqlCommand()
    command.query.append(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE = 'BASE TABLE' "
        "AND (@schema is NULL or TABLE_SCHEMA = ?) "
        "AND TABLE_NAME = ?;"
    )
    command.add_parameter(schema)
    command.add_parameter(table)
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


def _convert_value(value: Any | None, field: VectorStoreRecordField | None = None) -> str:
    """Add a value to the query builder."""
    if value is None:
        return "NULL"
    if field and isinstance(field, VectorStoreRecordVectorField):
        return f"CAST('{json.dumps(value)}' AS VECTOR({field.dimensions}))"
    match value:
        case str():
            return f"'{value}'"
        case bool():
            return "1" if value else "0"
        case int() | float():
            return f"'{value!s}'"
        case list():
            return f"'{json.dumps(value)}'"
        case dict():
            return f"{json.dumps(value)}"
        case bytes():
            return f"CONVERT(VARBINARY(MAX), '{value.hex()}')"
        case _:
            raise VectorStoreOperationException(f"Unsupported type: {type(value)}")


def _add_cast_check(value: str, field: VectorStoreRecordField) -> str:
    """Add a cast check to the value."""
    if isinstance(value, bytes):
        return f"CONVERT(VARBINARY(MAX), {value})"
    return value


def _cast_value(value: Any) -> str:
    """Add a cast check to the value."""
    match value:
        case str():
            return value
        case bool():
            return "1" if value else "0"
        case int() | float():
            return f"{value!s}"
        case list():
            return f"{json.dumps(value)}"
        case dict():
            return f"{json.dumps(value)}"
        case bytes():
            return f"{value.hex()}"
        case _:
            raise VectorStoreOperationException(f"Unsupported type: {type(value)}")


def _add_field_names(
    query_builder: StringBuilder,
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField] | None,
    prefix: str = "",
) -> StringBuilder:
    """Add a field name to the query builder."""
    # add the data and vector fields
    query_builder.append_list(
        [f"{prefix}{field.name}" for field in chain([key_field], data_fields, vector_fields or [])], end=" "
    )
    return query_builder


def _add_record_as_parameters(
    command: SqlCommand,
    record: dict[str, Any],
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
):
    """Add records as parameters to the command."""
    (
        command.add_parameter(_cast_value(record.get(field.name)))
        for field in chain([key_field], data_fields, vector_fields)
    )
    return command


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
    command.query.append_with_newline(
        f"DECLARE @UpsertedKeys TABLE (KeyColumn {_python_type_to_sql(key_field.property_type)});"
    )
    # start the MERGE statement
    command.query.append_table_name(schema, table, prefix="MERGE INTO", suffix="AS t", newline=True)
    # add the USING  VALUES clause
    with command.query.in_parenthesis("USING"):
        command.query.append(" VALUES ")
        for record in records:
            with command.query.in_parenthesis(end=",\n"):
                command.query.append_list(
                    [_add_cast_check("?", field) for field in chain([key_field], data_fields, vector_fields)],
                    end="",
                )

            # add the record as parameters
            [
                command.add_parameter(_cast_value(record.get(field.name)))
                for field in chain([key_field], data_fields, vector_fields)
            ]
        command.query.remove_last(2)  # remove the last comma
    # with the table column names
    with command.query.in_parenthesis("AS s", " "):
        _add_field_names(command.query, key_field, data_fields, vector_fields)
    # add the ON clause
    with command.query.in_parenthesis("ON", "\n"):
        command.query.append(f"t.{key_field.name} = s.{key_field.name}")
    # Set the Matched clause
    command.query.append_with_newline("WHEN MATCHED THEN")
    command.query.append("UPDATE SET ")
    command.query.append_list([f"t.{field.name} = s.{field.name}" for field in chain(data_fields, vector_fields)])
    # Set the Not Matched clause
    command.query.append_with_newline("WHEN NOT MATCHED THEN")
    with command.query.in_parenthesis("INSERT", " "):
        _add_field_names(command.query, key_field, data_fields, vector_fields)
    # add the closing parenthesis
    with command.query.in_parenthesis("VALUES", " \n"):
        _add_field_names(command.query, key_field, data_fields, vector_fields, prefix="s.")
    # add the closing parenthesis
    command.query.append_with_newline(f"OUTPUT inserted.{key_field.name} INTO @UpsertedKeys (KeyColumn);")
    command.query.append_with_newline("SELECT KeyColumn FROM @UpsertedKeys;")
    return command


def _build_select_query(
    schema: str,
    table: str,
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
    keys: Sequence[TKey],
    include_vectors: bool = True,
) -> SqlCommand:
    """Build the SELECT query based on the data model."""
    command = SqlCommand()
    # start the SELECT statement
    command.query.append_with_newline("SELECT ")
    # add the data and vector fields
    if include_vectors:
        _add_field_names(command.query, key_field, data_fields, vector_fields)
    else:
        _add_field_names(command.query, key_field, data_fields, None)
    # add the FROM clause
    command.query.append_table_name(schema, table, prefix=" FROM", newline=True)
    # add the WHERE clause
    if keys:
        command.query.append_with_newline(f"WHERE {key_field.name} IN ")
        with command.query.in_parenthesis():
            # add the keys
            command.query.append_list(["?"] * len(keys), sep=", ", end="")
            [command.add_parameter(_cast_value(key)) for key in keys]
    command.query.append(";")
    return command


def _build_delete_query(
    schema: str,
    table: str,
    key_field: VectorStoreRecordKeyField,
    keys: Sequence[TKey],
) -> SqlCommand:
    """Build the DELETE query based on the data model."""
    command = SqlCommand()
    # start the DELETE statement
    command.query.append_table_name(schema, table, prefix="DELETE FROM")
    # add the WHERE clause
    command.query.append_with_newline(f"WHERE {key_field.name} IN ")
    with command.query.in_parenthesis():
        # add the keys
        command.query.append_list((["?"] * len(keys)), sep=", ", end="")
        [command.add_parameter(_convert_value(key)) for key in keys]
    command.query.append(";")
    return command


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
    command = SqlCommand()
    # start the SELECT statement
    command.query.append("SELECT ")
    # add the data and vector fields
    _add_field_names(
        command.query, key_field, data_fields, vector_fields
    ) if options and options.include_vectors else _add_field_names(command.query, key_field, data_fields, None)
    # add the vector search clause
    if options.vector_field_name:
        vector_field = next(
            (field for field in vector_fields if field.name == options.vector_field_name),
            None,
        )
        if not vector_field:
            raise VectorStoreOperationException(
                f"Vector field '{options.vector_field_name}' not found in the data model."
            )
        if vector_field.distance_function:
            distance_function = DISTANCE_FUNCTION_MAP.get(vector_field.distance_function)
            if not distance_function:
                raise VectorStoreOperationException(
                    f"Distance function '{vector_field.distance_function}' not supported."
                )

            # add the ORDER BY clause
            asc: bool = DISTANCE_FUNCTION_DIRECTION_HELPER[vector_field.distance_function](0, 1)
        else:
            distance_function = "cosine"
            asc: bool = True

        command.query.append_with_newline(
            f", VECTOR_DISTANCE('{distance_function}', {vector_field.name}, CAST(? AS VECTOR({vector_field.dimensions}))) as {SCORE_FIELD_NAME}"  # noqa: E501
        )
        command.add_parameter(_cast_value(vector))
    # add the FROM clause
    command.query.append_table_name(schema, table, prefix=" FROM", newline=True)
    # add the WHERE clause
    if options.filter:
        filter_clause = _build_filter(options.filter)
        if filter_clause:
            command.query.append_with_newline(filter_clause)
    # add the ORDER BY clause
    command.query.append_with_newline(f"ORDER BY {SCORE_FIELD_NAME} {'ASC' if asc else 'DESC'}")
    command.query.append(f"OFFSET {options.skip} ROWS FETCH NEXT {options.top} ROWS ONLY")
    command.query.append(";")
    return command


def _build_filter(filters: VectorSearchFilter) -> str | None:
    """Build the filter query based on the data model."""
    query_builder = StringBuilder()
    if not filters.filters:
        return None
    query_builder.append("WHERE ")
    for filter in filters.filters:
        match filter:
            case EqualTo():
                query_builder.append_with_newline(f"{filter.field_name} = '{_cast_value(filter.value)}' AND")
            case AnyTagsEqualTo():
                query_builder.append_with_newline(f"'{_cast_value(filter.value)}' IN {filter.field_name} AND")
    # remove the last AND
    query_builder.remove_last(4)
    return str(query_builder)


class AzureSqlSettings(KernelBaseSettings):
    """Azure SQL settings.

    The settings are first loaded from environment variables with
    the prefix 'AZURE_SQL_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'AZURE_SQL_':
    - connection_string: str - The connection string of the Azure SQL Server.
        This value can be found in the Keys & Endpoint section when examining
        your resource from the Azure portal.
        The advice is to use a password-less setup, see
        https://learn.microsoft.com/en-us/azure/azure-sql/database/azure-sql-passwordless-migration-python?view=azuresql&preserve-view=true&tabs=sign-in-azure-cli%2Cazure-portal-create%2Cazure-portal-assign%2Capp-service-identity#update-the-local-connection-configuration for more info.
        (Env var name: AZURE_SQL_CONNECTION_STRING)
    """  # noqa: E501

    env_prefix: ClassVar[str] = "AZURE_SQL_"

    connection_string: SecretStr

    @field_validator("connection_string", mode="before")
    @classmethod
    def validate_connection_string(cls, value: str) -> str:
        """Validate the connection string.

        The LongAsMax=yes option is added to the connection string if it is not present.
        This is needed to supply vectors as query parameters.

        """
        if "LongAsMax=yes" not in value:
            return f"{value};LongAsMax=yes"
        return value


async def get_mssql_connection(settings: AzureSqlSettings) -> pyodbc.Connection:
    """Get a connection to the Azure SQL database."""
    mssql_connection_string = settings.connection_string.get_secret_value()
    if any(s in mssql_connection_string.lower() for s in ["uid"]):
        attrs_before = None
    else:
        async with DefaultAzureCredential(exclude_interactive_browser_credential=False) as credential:
            # Get the access token
            token_bytes = (await credential.get_token("https://database.windows.net/.default")).token.encode(
                "UTF-16-LE"
            )
            token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
            SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
            attrs_before = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}

    return pyodbc.connect(mssql_connection_string, attrs_before=attrs_before)


@experimental
class AzureSqlCollection(
    VectorSearchBase[TKey, TModel],
    VectorizedSearchMixin[TModel],
    Generic[TKey, TModel],
):
    """SQL collection implementation."""

    connection: pyodbc.Connection | None = None
    supported_key_types: ClassVar[list[str] | None] = ["str", "int"]
    supported_vector_types: ClassVar[list[str] | None] = ["float"]
    settings: AzureSqlSettings | None = None

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        connection_string: str | None = None,
        connection: pyodbc.Connection | None = None,
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
                settings = AzureSqlSettings.create(
                    connection_string=connection_string,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise VectorStoreOperationException(
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

    # region: VectorStoreRecordCollection implementation

    @override
    async def __aenter__(self) -> Self:
        # If the connection pool was not provided, create a new one.
        if not self.connection:
            self.connection = await get_mssql_connection(self.settings)
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
        command = _build_merge_query(
            *self._get_schema_and_table(),
            self.data_model_definition.key_field,
            [
                field
                for field in self.data_model_definition.fields.values()
                if isinstance(field, VectorStoreRecordDataField)
            ],
            self.data_model_definition.vector_fields,
            records,
        )
        # Execute the merge query
        results = self._execute_merge_query(command)
        # Extract the keys from the result
        keys = [row[0] for row in results]
        if not keys:
            raise VectorStoreOperationException("No keys were returned from the merge query.")
        # Return the keys
        return keys

    def _execute_merge_query(self, command: SqlCommand | str) -> list[Row]:
        with self.connection.cursor() as cur:
            if isinstance(command, str):
                cur.execute(command)
            elif isinstance(command, SqlCommand) and command.is_execute_many:
                cur.executemany(*command.to_execute())
            else:
                cur.execute(*command.to_execute())
            try:
                return cur.fetchall()
            except pyodbc.ProgrammingError:
                # No rows were returned
                pass
            while cur.nextset():
                try:
                    return cur.fetchall()
                except pyodbc.ProgrammingError:
                    # No keys were returned
                    continue
        return []

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[dict[str, Any]] | None:
        """Get records from the database.

        Args:
            keys: The keys to get.
            **kwargs: Additional arguments.

        Returns:
            The records from the store, not deserialized.
        """
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")
        if not keys:
            return None
        include_vectors = kwargs.get("include_vectors", True)
        query = _build_select_query(
            *self._get_schema_and_table(),
            self.data_model_definition.key_field,
            [
                field
                for field in self.data_model_definition.fields.values()
                if isinstance(field, VectorStoreRecordDataField)
            ],
            self.data_model_definition.vector_fields,
            keys,
            include_vectors,
        )
        with self.connection.cursor() as cur:
            cur.execute(*query.to_execute())
            try:
                col_names = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                records = [{col: row.__getattribute__(col) for col in col_names} for row in rows] if rows else None
                if not records:
                    return None
                for field in self.data_model_definition.vector_field_names:
                    for record in records:
                        if field in record:
                            record[field] = json.loads(record[field])
                return records
            except pyodbc.ProgrammingError:
                # No rows were returned
                return None

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
        self, create_if_not_exists: bool = True, queries: list[str] | None = None, **kwargs: Any
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
            schema, _ = self._get_schema_and_table()
            cursor.execute(*_build_select_table_names_query(schema=schema).to_execute())
            row = cursor.fetchone()
            return bool(row)

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection."""
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        with self.connection.cursor() as cur:
            schema, table = self._get_schema_and_table()
            cur.execute(*_build_delete_table_query(schema=schema, table=table).to_execute())
            logger.info(f"SqlServer table '{self.collection_name}' deleted successfully.")

    # region: VectorSearchBase implementation

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

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

        with self.connection.cursor() as cur:
            cur.execute(*query.to_execute())
            # Fetch all results to get total count.
            num_rows = cur.rowcount if cur.rowcount != -1 else None
            col_names = [desc[0] for desc in cur.description]

            async def _fetch_records(cursor: pyodbc.Cursor, col_names: list[str]) -> AsyncIterable[dict[str, Any]]:
                row = cursor.fetchone()
                while row:
                    record = {col: row.__getattribute__(col) for col in col_names}
                    for field in self.data_model_definition.vector_field_names:
                        if field in record:
                            record[field] = json.loads(record[field])
                    yield record
                    row = cursor.fetchone()
                    await asyncio.sleep(0)

            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(_fetch_records(cur, col_names), options),
                total_count=num_rows,
            )

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.pop(SCORE_FIELD_NAME, None)

    # endregion
