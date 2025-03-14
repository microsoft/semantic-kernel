# Copyright (c) Microsoft. All rights reserved.


import json
import logging
import re
import struct
import sys
from collections.abc import AsyncGenerator, Sequence
from itertools import chain
from typing import Any, ClassVar, Generic, TypeVar

import pyodbc
from azure.identity.aio import DefaultAzureCredential
from pydantic import SecretStr, ValidationError

from semantic_kernel.connectors.memory.postgres.utils import (
    convert_row_to_dict,
)
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
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

logger: logging.Logger = logging.getLogger(__name__)


DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_DISTANCE: "cosine",
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.DOT_PROD: "dot",
}


def python_type_to_sql(python_type_str: str | None, is_key: bool = False) -> str | None:
    """Convert a string representation of a Python type to a SQL data type.

    Args:
        python_type_str: The string representation of the Python type (e.g., "int", "List[str]").

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
        sql_element_type = python_type_to_sql(element_type_str)
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
) -> str:
    """Build the CREATE TABLE query based on the data model."""
    query_builder = []
    if if_not_exists:
        query_builder.append(f"IF OBJECT_ID(N'{schema}.{table}', N'U') IS NULL\n")
    query_builder.append("BEGIN\n")
    query_builder.append(f"CREATE TABLE {schema}.{table} (\n")
    # add the key field
    query_builder.append(f'"{key_field.name}" {python_type_to_sql(key_field.property_type, is_key=True)} NOT NULL,\n')
    # add the data fields
    [query_builder.append(f'"{field.name}" {python_type_to_sql(field.property_type)} NULL,\n') for field in data_fields]
    # add the vector fields
    for field in vector_fields:
        if field.dimensions is None:
            raise ValueError(f"Vector dimensions are not defined for field '{field.name}'")
        query_builder.append(f'"{field.name}" VECTOR({field.dimensions}) NULL,\n')
    # set the primary key
    query_builder.append(f'PRIMARY KEY ("{key_field.name}")\n')
    query_builder.append(");\n")
    query_builder.append("END\n")
    return f"{(' ').join(query_builder)}"


def _build_delete_table_query(
    schema: str,
    table: str,
) -> str:
    """Build the DELETE TABLE query based on the data model."""
    return f"DROP TABLE IF EXISTS {schema}.{table};\n"


def _build_select_table_query(
    schema: str,
    table: str,
) -> str:
    """Build the SELECT TABLE query based on the data model."""
    return (
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE = 'BASE TABLE' "
        f"AND (@schema is NULL or TABLE_SCHEMA = {schema}) "
        f"AND TABLE_NAME = {table}"
    )


def _build_select_table_names_query(
    schema: str | None = None,
) -> str:
    """Build the SELECT TABLE NAMES query based on the data model."""
    if schema:
        return (
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE' "
            f"AND (@schema is NULL or TABLE_SCHEMA = {schema}) "
        )
    return "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' "


def _add_value(value: Any | None, field: VectorStoreRecordField) -> str:
    """Add a value to the query builder."""
    if value is None:
        return "NULL"
    if isinstance(field, VectorStoreRecordVectorField):
        return f"CAST('{json.dumps(value)}' AS VECTOR({field.dimensions})),"
    match value:
        case str():
            return f"'{value}',"
        case bool():
            return "1," if value else "0,"
        case int() | float():
            return f"'{value!s}',"
        case list() | dict():
            return f"'{json.dumps(value)}',"
        case bytes():
            return f"CONVERT(VARBINARY(MAX), '{value.hex()}'),"
        case _:
            raise VectorStoreOperationException(f"Unsupported type: {type(value)}")


def _record_to_sql_string(
    record: dict[str, Any],
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
) -> str:
    """Convert a record to a SQL string."""
    output = []
    # add the key field
    output.append(_add_value(record[key_field.name], key_field))
    # add the data and vector fields
    for field in chain(data_fields, vector_fields):
        if field.name in record:
            output.append(_add_value(record[field.name], field))
        else:
            output.append("NULL,")
    # remove the last comma
    output[-1] = output[-1][:-1]
    # add the closing parenthesis
    output.append("),\n")
    return "".join(output)


def _add_field_names(
    query_builder: list[str],
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
    prefix: str = "",
) -> list[str]:
    """Add a field name to the query builder."""
    # add the column names
    query_builder.append(f"{prefix}{key_field.name},")
    # add the data fields
    [query_builder.append(f"{prefix}{field.name},") for field in data_fields]
    # add the vector fields
    [query_builder.append(f"{prefix}{field.name},") for field in vector_fields]
    # remove the last comma
    query_builder[-1] = query_builder[-1][:-1]
    return query_builder


def _build_merge_table_query(
    schema: str,
    table: str,
    key_field: VectorStoreRecordKeyField,
    data_fields: list[VectorStoreRecordDataField],
    vector_fields: list[VectorStoreRecordVectorField],
    records: Sequence[dict[str, Any]],
) -> str:
    """Build the MERGE TABLE query based on the data model."""
    query_builder = []
    query_builder.append(f"DECLARE @InsertedKeys TABLE (KeyColumn {python_type_to_sql(key_field.property_type)});\n")
    query_builder.append(f"MERGE INTO {schema}.{table} AS t\n")
    query_builder.append("USING (VALUES\n")
    # add the values from the records
    [query_builder.append(_record_to_sql_string(record, key_field, data_fields, vector_fields)) for record in records]
    # remove the last comma and newline
    query_builder[-1] = query_builder[-1][:-2]
    query_builder.append(") AS s (")
    _add_field_names(query_builder, key_field, data_fields, vector_fields)
    # add the closing parenthesis
    query_builder.append(")\n")
    # add the ON clause
    query_builder.append(f"ON (t.{key_field.name} = s.{key_field.name})\n")
    query_builder.append("WHEN MATCHED THEN\n")
    query_builder.append("UPDATE SET ")
    # add the data fields
    for field in chain(data_fields, vector_fields):
        query_builder.append(f"t.{field.name} = s.{field.name},")
    # remove the last comma
    query_builder[-1] = query_builder[-1][:-1]
    query_builder.append("\n")
    query_builder.append("WHEN NOT MATCHED THEN\n")
    query_builder.append("INSERT (")
    # add the field names
    _add_field_names(query_builder, key_field, data_fields, vector_fields)
    # add the closing parenthesis
    query_builder.append(")\n")
    query_builder.append("VALUES (")
    # add the field names
    _add_field_names(query_builder, key_field, data_fields, vector_fields, prefix="s.")
    # add the closing parenthesis
    query_builder.append(")\n")
    query_builder.append(f"OUTPUT inserted.{key_field.name} INTO @InsertedKeys (KeyColumn);\n")
    query_builder.append("SELECT KeyColumn FROM @InsertedKeys;\n")
    return f"{(' ').join(query_builder)}"


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


async def get_mssql_connection(settings: AzureSqlSettings) -> pyodbc.Connection:
    """Get a connection to the Azure SQL database."""
    mssql_connection_string = settings.connection_string.get_secret_value()
    if any(s in mssql_connection_string.lower() for s in ["uid"]):
        attrs_before = None
    else:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        token_bytes = (await credential.get_token("https://database.windows.net/.default")).token.encode("UTF-16-LE")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
        attrs_before = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}

    conn = pyodbc.connect(mssql_connection_string, attrs_before=attrs_before)

    return conn


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
            connection: The connection pool.
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
        schema, table = self._get_schema_and_table()
        with self.connection.cursor() as cur:
            cur.execute(
                _build_merge_table_query(
                    schema,
                    table,
                    self.data_model_definition.key_field,
                    [
                        field
                        for field in self.data_model_definition.fields.values()
                        if isinstance(field, VectorStoreRecordDataField)
                    ],
                    self.data_model_definition.vector_fields,
                    records,
                )
            )
            inserted_keys = cur.fetchall()
            if not inserted_keys:
                return []
            return [key[0] for key in inserted_keys]

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

        # fields = [(field.name, field) for field in self.data_model_definition.fields.values()]
        # async with self.connection.connection() as conn, conn.cursor() as cur:
        #     await cur.execute(
        #         sql.SQL("SELECT {select_list} FROM {schema}.{table} WHERE {key_name} IN ({keys})").format(
        #             select_list=sql.SQL(", ").join(sql.Identifier(name) for (name, _) in fields),
        #             schema=sql.Identifier(self.db_schema),
        #             table=sql.Identifier(self.collection_name),
        #             key_name=sql.Identifier(self.data_model_definition.key_field.name),
        #             keys=sql.SQL(", ").join(sql.Literal(key) for key in keys),
        #         )
        #     )
        #     rows = await cur.fetchall()
        #     if not rows:
        #         return None
        #     return [convert_row_to_dict(row, fields) for row in rows]

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records with the given keys.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.
        """
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        # async with (
        #     self.connection.connection() as conn,
        #     conn.transaction(),
        #     conn.cursor() as cur,
        # ):
        #     # Split the keys into batches
        #     max_rows_per_transaction = self._settings.max_rows_per_transaction
        #     for i in range(0, len(keys), max_rows_per_transaction):
        #         key_batch = keys[i : i + max_rows_per_transaction]

        #         # Execute the DELETE statement for each batch
        #         await cur.execute(
        #             sql.SQL("DELETE FROM {schema}.{table} WHERE {name} IN ({keys})").format(
        #                 schema=sql.Identifier(self.db_schema),
        #                 table=sql.Identifier(self.collection_name),
        #                 name=sql.Identifier(self.data_model_definition.key_field.name),
        #                 keys=sql.SQL(", ").join(sql.Literal(key) for key in key_batch),
        #             )
        #         )

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

        schema, table = self._get_schema_and_table()
        data_fields = [
            field
            for field in self.data_model_definition.fields.values()
            if isinstance(field, VectorStoreRecordDataField)
        ]
        create_table_query = _build_create_table_query(
            schema=schema,
            table=table,
            key_field=self.data_model_definition.key_field,
            data_fields=data_fields,
            vector_fields=self.data_model_definition.vector_fields,
            if_not_exists=create_if_not_exists,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(create_table_query)
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
            cursor.execute(_build_select_table_names_query(schema=schema))
            row = cursor.fetchone()
            return bool(row)

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection."""
        if self.connection is None:
            raise VectorStoreOperationException("connection is not available, use the collection as a context manager.")

        with self.connection.cursor() as cur:
            schema, table = self._get_schema_and_table()
            cur.execute(_build_delete_table_query(schema=schema, table=table))
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
            query, params, return_fields = self._construct_vector_query(vector, options, **kwargs)
        elif search_text:
            raise VectorSearchExecutionException("Text search not supported.")
        elif vectorizable_text:
            raise VectorSearchExecutionException("Vectorizable text search not supported.")

        if options.include_total_count:
            async with self.connection.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                # Fetch all results to get total count.
                rows = await cur.fetchall()
                row_dicts = [convert_row_to_dict(row, return_fields) for row in rows]
                return KernelSearchResults(
                    results=self._get_vector_search_results_from_results(row_dicts, options), total_count=len(row_dicts)
                )
        else:
            # Use an asynchronous generator to fetch and yield results
            connection = self.connection

            async def fetch_results() -> AsyncGenerator[dict[str, Any], None]:
                async with connection.connection() as conn, conn.cursor() as cur:
                    await cur.execute(query, params)
                    async for row in cur:
                        yield convert_row_to_dict(row, return_fields)

            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(fetch_results(), options),
                total_count=None,
            )

    # def _construct_vector_query(
    #     self,
    #     vector: list[float | int],
    #     options: VectorSearchOptions,
    #     **kwargs: Any,
    # ) -> tuple[sql.Composed, list[Any], list[tuple[str, VectorStoreRecordField | None]]]:
    #     """Construct a vector search query.

    #     Args:
    #         vector: The vector to search for.
    #         options: The search options.
    #         **kwargs: Additional arguments.

    #     Returns:
    #         The query, parameters, and the fields representing the columns in the result.
    #     """
    #     # Get the vector field we will be searching against,
    #     # defaulting to the first vector field if not specified
    #     vector_fields = self.data_model_definition.vector_fields
    #     if not vector_fields:
    #         raise VectorSearchExecutionException("No vector fields defined.")
    #     if options.vector_field_name:
    #         vector_field = next((f for f in vector_fields if f.name == options.vector_field_name), None)
    #         if not vector_field:
    #             raise VectorSearchExecutionException(f"Vector field '{options.vector_field_name}' not found.")
    #     else:
    #         vector_field = vector_fields[0]

    #     # Default to cosine distance if not set
    #     distance_function = vector_field.distance_function or DistanceFunction.COSINE_DISTANCE
    #     ops_str = get_vector_distance_ops_str(distance_function)

    #     # Select all fields except all vector fields if include_vectors is False
    #     select_list = self.data_model_definition.get_field_names(include_vector_fields=options.include_vectors)

    #     where_clause = self._build_where_clauses_from_filter(options.filter)

    #     query = sql.SQL("SELECT {select_list}, {vec_col} {dist_op} %s as {dist_col} FROM {schema}.{table}").format(
    #         select_list=sql.SQL(", ").join(sql.Identifier(name) for name in select_list),
    #         vec_col=sql.Identifier(vector_field.name),
    #         dist_op=sql.SQL(ops_str),
    #         dist_col=sql.Identifier(self._distance_column_name),
    #         schema=sql.Identifier(self.db_schema),
    #         table=sql.Identifier(self.collection_name),
    #     )

    #     if where_clause:
    #         query += where_clause

    #     query += sql.SQL(" ORDER BY {dist_col} LIMIT {limit}").format(
    #         dist_col=sql.Identifier(self._distance_column_name),
    #         limit=sql.Literal(options.top),
    #     )

    #     if options.skip:
    #         query += sql.SQL(" OFFSET {offset}").format(offset=sql.Literal(options.skip))

    #     # For cosine similarity, we need to take 1 - cosine distance.
    #     # However, we can't use an expression in the ORDER BY clause or else the index won't be used.
    #     # Instead we'll wrap the query in a subquery and modify the distance in the outer query.
    #     if distance_function == DistanceFunction.COSINE_SIMILARITY:
    #         query = sql.SQL(
    #             "SELECT subquery.*, 1 - subquery.{subquery_dist_col} AS {dist_col} FROM ({subquery}) AS subquery"
    #         ).format(
    #             subquery_dist_col=sql.Identifier(self._distance_column_name),
    #             dist_col=sql.Identifier(self._distance_column_name),
    #             subquery=query,
    #         )

    #     # For inner product, we need to take -1 * inner product.
    #     # However, we can't use an expression in the ORDER BY clause or else the index won't be used.
    #     # Instead we'll wrap the query in a subquery and modify the distance in the outer query.
    #     if distance_function == DistanceFunction.DOT_PROD:
    #         query = sql.SQL(
    #             "SELECT subquery.*, -1 * subquery.{subquery_dist_col} AS {dist_col} FROM ({subquery}) AS subquery"
    #         ).format(
    #             subquery_dist_col=sql.Identifier(self._distance_column_name),
    #             dist_col=sql.Identifier(self._distance_column_name),
    #             subquery=query,
    #         )

    #     # Convert the vector to a string for the query
    #     params = ["[" + ",".join([str(float(v)) for v in vector]) + "]"]

    #     return (
    #         query,
    #         params,
    #         [
    #             *((name, f) for (name, f) in self.data_model_definition.fields.items() if name in select_list),
    #             (self._distance_column_name, None),
    #         ],
    #     )

    # def _build_where_clauses_from_filter(self, filters: VectorSearchFilter | None) -> sql.Composed | None:
    #     """Build the WHERE clause for the search query from the filter in the search options.

    #     Args:
    #         filters: The filters.

    #     Returns:
    #         The WHERE clause.
    #     """
    #     if not filters or not filters.filters:
    #         return None

    #     where_clauses = []
    #     for filter in filters.filters:
    #         match filter:
    #             case EqualTo():
    #                 where_clauses.append(
    #                     sql.SQL("{field} = {value}").format(
    #                         field=sql.Identifier(filter.field_name),
    #                         value=sql.Literal(filter.value),
    #                     )
    #                 )
    #             case AnyTagsEqualTo():
    #                 where_clauses.append(
    #                     sql.SQL("{field} @> ARRAY[{value}::TEXT").format(
    #                         field=sql.Identifier(filter.field_name),
    #                         value=sql.Literal(filter.value),
    #                     )
    #                 )
    #             case _:
    #                 raise ValueError(f"Unsupported filter: {filter}")

    #     return sql.SQL("WHERE {clause}").format(clause=sql.SQL(" AND ").join(where_clauses))

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.pop("score", None)

    # endregion
