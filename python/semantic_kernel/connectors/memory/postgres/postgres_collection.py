# Copyright (c) Microsoft. All rights reserved.

import logging
import random
import string
import sys
from collections.abc import AsyncGenerator, Sequence
from typing import Any, ClassVar, Generic

from psycopg import sql
from psycopg_pool import AsyncConnectionPool
from pydantic import PrivateAttr

from semantic_kernel.connectors.memory.postgres.constants import (
    DEFAULT_SCHEMA,
    DISTANCE_COLUMN_NAME,
    MAX_DIMENSIONALITY,
)
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings
from semantic_kernel.connectors.memory.postgres.utils import (
    convert_dict_to_row,
    convert_row_to_dict,
    get_vector_distance_ops_str,
    get_vector_index_ops_str,
    python_type_to_postgres,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDefinition,
    VectorStoreRecordField,
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
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorStoreModelValidationError, VectorStoreOperationException
from semantic_kernel.exceptions.vector_store_exceptions import VectorSearchExecutionException
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


logger: logging.Logger = logging.getLogger(__name__)


@experimental
class PostgresCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """PostgreSQL collection implementation."""

    connection_pool: AsyncConnectionPool | None = None
    db_schema: str = DEFAULT_SCHEMA
    supported_key_types: ClassVar[list[str] | None] = ["str", "int"]
    supported_vector_types: ClassVar[list[str] | None] = ["float"]
    _distance_column_name: str = PrivateAttr(DISTANCE_COLUMN_NAME)

    _settings: PostgresSettings = PrivateAttr()
    """Postgres settings"""

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        connection_pool: AsyncConnectionPool | None = None,
        db_schema: str = DEFAULT_SCHEMA,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        settings: PostgresSettings | None = None,
    ):
        """Initialize the collection.

        Args:
            collection_name: The name of the collection, which corresponds to the table name.
            data_model_type: The type of the data model.
            data_model_definition: The data model definition.
            connection_pool: The connection pool.
            db_schema: The database schema.
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            settings: The settings for creating a new connection pool. If not provided, the settings will be created
                from the environment.
        """
        super().__init__(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
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
        while distance_column_name in self.data_model_definition.fields:
            # Reset the distance column name, ensuring no collision with existing model fields
            # Avoid bandit B311 - random is not used for a security/cryptographic purpose
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))  # nosec B311
            distance_column_name = f"{DISTANCE_COLUMN_NAME}_{suffix}"
            tries += 1
            if tries > 10:
                raise VectorStoreModelValidationError("Unable to generate a unique distance column name.")
        self._distance_column_name = distance_column_name

    # region: VectorStoreRecordCollection implementation

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
        for field in self.data_model_definition.vector_fields:
            if field.dimensions is not None:
                if field.dimensions > MAX_DIMENSIONALITY:
                    raise VectorStoreModelValidationError(
                        f"Dimensionality of {field.dimensions} exceeds the maximum allowed "
                        f"value of {MAX_DIMENSIONALITY}."
                    )
                if field.dimensions <= 0:
                    raise VectorStoreModelValidationError("Dimensionality must be a positive integer. ")

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

        keys = []
        async with (
            self.connection_pool.connection() as conn,
            conn.transaction(),
            conn.cursor() as cur,
        ):
            # Split the records into batches
            max_rows_per_transaction = self._settings.max_rows_per_transaction
            for i in range(0, len(records), max_rows_per_transaction):
                record_batch = records[i : i + max_rows_per_transaction]

                fields = list(self.data_model_definition.fields.items())

                row_values = [convert_dict_to_row(record, fields) for record in record_batch]

                # Execute the INSERT statement for each batch
                await cur.executemany(
                    sql.SQL(
                        "INSERT INTO {schema}.{table} ({col_names}) VALUES ({placeholders}) "
                        "ON CONFLICT ({key_name}) DO UPDATE SET {update_columns}"
                    ).format(
                        schema=sql.Identifier(self.db_schema),
                        table=sql.Identifier(self.collection_name),
                        col_names=sql.SQL(", ").join(sql.Identifier(field.name) for _, field in fields),
                        placeholders=sql.SQL(", ").join(sql.Placeholder() * len(fields)),
                        key_name=sql.Identifier(self.data_model_definition.key_field.name),
                        update_columns=sql.SQL(", ").join(
                            sql.SQL("{field} = EXCLUDED.{field}").format(field=sql.Identifier(field.name))
                            for _, field in fields
                            if field.name != self.data_model_definition.key_field.name
                        ),
                    ),
                    row_values,
                )
                keys.extend(record.get(self.data_model_definition.key_field.name) for record in record_batch)
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
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        fields = [(field.name, field) for field in self.data_model_definition.fields.values()]
        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                sql.SQL("SELECT {select_list} FROM {schema}.{table} WHERE {key_name} IN ({keys})").format(
                    select_list=sql.SQL(", ").join(sql.Identifier(name) for (name, _) in fields),
                    schema=sql.Identifier(self.db_schema),
                    table=sql.Identifier(self.collection_name),
                    key_name=sql.Identifier(self.data_model_definition.key_field.name),
                    keys=sql.SQL(", ").join(sql.Literal(key) for key in keys),
                )
            )
            rows = await cur.fetchall()
            if not rows:
                return None
            return [convert_row_to_dict(row, fields) for row in rows]

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
                        name=sql.Identifier(self.data_model_definition.key_field.name),
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

        for field_name, field in self.data_model_definition.fields.items():
            if not field.property_type:
                raise ValueError(f"Property type is not defined for field '{field_name}'")

            # If the property type represents a Python type, convert it to a PostgreSQL type
            property_type = python_type_to_postgres(field.property_type) or field.property_type.upper()

            # For Vector fields with dimensions, use pgvector's VECTOR type
            # Note that other vector types are supported in pgvector (e.g. halfvec),
            # but would need to be created outside of this method.
            if isinstance(field, VectorStoreRecordVectorField) and field.dimensions:
                column_definitions.append(
                    sql.SQL("{name} VECTOR({dimensions})").format(
                        name=sql.Identifier(field_name), dimensions=sql.Literal(field.dimensions)
                    )
                )
            elif isinstance(field, VectorStoreRecordKeyField):
                # Use the property_type directly for key fields
                column_definitions.append(
                    sql.SQL("{name} {col_type} PRIMARY KEY").format(
                        name=sql.Identifier(field_name), col_type=sql.SQL(property_type)
                    )
                )
            else:
                # Use the property_type directly for other types
                column_definitions.append(
                    sql.SQL("{name} {col_type}").format(
                        name=sql.Identifier(field_name), col_type=sql.SQL(property_type)
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
        for vector_field in self.data_model_definition.vector_fields:
            if vector_field.index_kind:
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
    async def delete_collection(self, **kwargs: Any) -> None:
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

    async def _create_index(self, table_name: str, vector_field: VectorStoreRecordVectorField) -> None:
        """Create an index on a column in the table.

        Args:
            table_name: The name of the table.
            vector_field: The vector field definition that the index is based on.
        """
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        column_name = vector_field.name
        index_name = f"{table_name}_{column_name}_idx"

        # Only support creating HNSW indexes through the vector store
        if vector_field.index_kind != IndexKind.HNSW:
            raise VectorStoreOperationException(
                f"Unsupported index kind: {vector_field.index_kind}. "
                "If you need to create an index of this type, please do so manually. "
                "Only HNSW indexes are supported through the vector store."
            )

        # Require the distance function to be set for HNSW indexes
        if not vector_field.distance_function:
            raise VectorStoreOperationException(
                "Distance function must be set for HNSW indexes. "
                "Please set the distance function in the vector field definition."
            )

        ops_str = get_vector_index_ops_str(vector_field.distance_function)

        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(
                sql.SQL("CREATE INDEX {index_name} ON {schema}.{table} USING {index_kind} ({column_name} {op})").format(
                    index_name=sql.Identifier(index_name),
                    schema=sql.Identifier(self.db_schema),
                    table=sql.Identifier(table_name),
                    index_kind=sql.SQL(vector_field.index_kind),
                    column_name=sql.Identifier(column_name),
                    op=sql.SQL(ops_str),
                )
            )
            await conn.commit()

        logger.info(f"Index '{index_name}' created successfully on column '{column_name}'.")

    # endregion
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
        if self.connection_pool is None:
            raise VectorStoreOperationException(
                "Connection pool is not available, use the collection as a context manager."
            )

        if vector is not None:
            query, params, return_fields = self._construct_vector_query(vector, options, **kwargs)
        elif search_text:
            raise VectorSearchExecutionException("Text search not supported.")
        elif vectorizable_text:
            raise VectorSearchExecutionException("Vectorizable text search not supported.")

        if options.include_total_count:
            async with self.connection_pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, params)
                # Fetch all results to get total count.
                rows = await cur.fetchall()
                row_dicts = [convert_row_to_dict(row, return_fields) for row in rows]
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
                        yield convert_row_to_dict(row, return_fields)

            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(fetch_results(), options),
                total_count=None,
            )

    def _construct_vector_query(
        self,
        vector: list[float | int],
        options: VectorSearchOptions,
        **kwargs: Any,
    ) -> tuple[sql.Composed, list[Any], list[tuple[str, VectorStoreRecordField | None]]]:
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
        vector_fields = self.data_model_definition.vector_fields
        if not vector_fields:
            raise VectorSearchExecutionException("No vector fields defined.")
        if options.vector_field_name:
            vector_field = next((f for f in vector_fields if f.name == options.vector_field_name), None)
            if not vector_field:
                raise VectorSearchExecutionException(f"Vector field '{options.vector_field_name}' not found.")
        else:
            vector_field = vector_fields[0]

        # Default to cosine distance if not set
        distance_function = vector_field.distance_function or DistanceFunction.COSINE_DISTANCE
        ops_str = get_vector_distance_ops_str(distance_function)

        # Select all fields except all vector fields if include_vectors is False
        select_list = self.data_model_definition.get_field_names(include_vector_fields=options.include_vectors)

        where_clause = self._build_where_clauses_from_filter(options.filter)

        query = sql.SQL("SELECT {select_list}, {vec_col} {dist_op} %s as {dist_col} FROM {schema}.{table}").format(
            select_list=sql.SQL(", ").join(sql.Identifier(name) for name in select_list),
            vec_col=sql.Identifier(vector_field.name),
            dist_op=sql.SQL(ops_str),
            dist_col=sql.Identifier(self._distance_column_name),
            schema=sql.Identifier(self.db_schema),
            table=sql.Identifier(self.collection_name),
        )

        if where_clause:
            query += where_clause

        query += sql.SQL(" ORDER BY {dist_col} LIMIT {limit}").format(
            dist_col=sql.Identifier(self._distance_column_name),
            limit=sql.Literal(options.top),
        )

        if options.skip:
            query += sql.SQL(" OFFSET {offset}").format(offset=sql.Literal(options.skip))

        # For cosine similarity, we need to take 1 - cosine distance.
        # However, we can't use an expression in the ORDER BY clause or else the index won't be used.
        # Instead we'll wrap the query in a subquery and modify the distance in the outer query.
        if distance_function == DistanceFunction.COSINE_SIMILARITY:
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
        if distance_function == DistanceFunction.DOT_PROD:
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
                *((name, f) for (name, f) in self.data_model_definition.fields.items() if name in select_list),
                (self._distance_column_name, None),
            ],
        )

    def _build_where_clauses_from_filter(self, filters: VectorSearchFilter | None) -> sql.Composed | None:
        """Build the WHERE clause for the search query from the filter in the search options.

        Args:
            filters: The filters.

        Returns:
            The WHERE clause.
        """
        if not filters or not filters.filters:
            return None

        where_clauses = []
        for filter in filters.filters:
            match filter:
                case EqualTo():
                    where_clauses.append(
                        sql.SQL("{field} = {value}").format(
                            field=sql.Identifier(filter.field_name),
                            value=sql.Literal(filter.value),
                        )
                    )
                case AnyTagsEqualTo():
                    where_clauses.append(
                        sql.SQL("{field} @> ARRAY[{value}::TEXT").format(
                            field=sql.Identifier(filter.field_name),
                            value=sql.Literal(filter.value),
                        )
                    )
                case _:
                    raise ValueError(f"Unsupported filter: {filter}")

        return sql.SQL("WHERE {clause}").format(clause=sql.SQL(" AND ").join(where_clauses))

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return {k: v for (k, v) in result.items() if k != self._distance_column_name}

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result.pop(self._distance_column_name, None)

    # endregion
