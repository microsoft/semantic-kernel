# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from psycopg import sql
from psycopg_pool import AsyncConnectionPool
from pydantic import PrivateAttr

from semantic_kernel.connectors.memory.postgres.constants import DEFAULT_SCHEMA, MAX_DIMENSIONALITY
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings
from semantic_kernel.connectors.memory.postgres.utils import (
    convert_dict_to_row,
    convert_row_to_dict,
    get_vector_index_ops_str,
    python_type_to_postgres,
)
from semantic_kernel.data.const import IndexKind
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions import (
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TKey = TypeVar("TKey", str, int)
TModel = TypeVar("TModel")

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class PostgresCollection(VectorStoreRecordCollection[TKey, TModel]):
    """PostgreSQL collection implementation."""

    connection_pool: AsyncConnectionPool | None = None
    db_schema: str = DEFAULT_SCHEMA
    supported_key_types: ClassVar[list[str] | None] = ["str", "int"]
    supported_vector_types: ClassVar[list[str] | None] = ["float"]

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
        )

        self._settings = settings or PostgresSettings.create(
            env_file_path=env_file_path, env_file_encoding=env_file_encoding
        )

    @override
    async def __aenter__(self) -> "PostgresCollection":
        # If the connection pool was not provided, create a new one.
        if not self.connection_pool:
            self.connection_pool = await self._settings.create_connection_pool()
            self.managed_client = True
        return self

    @override
    async def __aexit__(self, *args):
        if self.managed_client and self.connection_pool:
            await self.connection_pool.close()
            # If the pool was created by the collection, set it to None to enable reusing the collection.
            if self._settings:
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
                    sql.SQL("INSERT INTO {}.{} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}").format(
                        sql.Identifier(self.db_schema),
                        sql.Identifier(self.collection_name),
                        sql.SQL(", ").join(sql.Identifier(field.name) for _, field in fields),
                        sql.SQL(", ").join(sql.Placeholder() * len(fields)),
                        sql.Identifier(self.data_model_definition.key_field.name),
                        sql.SQL(", ").join(
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
                sql.SQL("SELECT {} FROM {}.{} WHERE {} IN ({})").format(
                    sql.SQL(", ").join(sql.Identifier(name) for (name, _) in fields),
                    sql.Identifier(self.db_schema),
                    sql.Identifier(self.collection_name),
                    sql.Identifier(self.data_model_definition.key_field.name),
                    sql.SQL(", ").join(sql.Literal(key) for key in keys),
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
                    sql.SQL("DELETE FROM {}.{} WHERE {} IN ({})").format(
                        sql.Identifier(self.db_schema),
                        sql.Identifier(self.collection_name),
                        sql.Identifier(self.data_model_definition.key_field.name),
                        sql.SQL(", ").join(sql.Literal(key) for key in key_batch),
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
                    sql.SQL("{} VECTOR({})").format(sql.Identifier(field_name), sql.Literal(field.dimensions))
                )
            elif isinstance(field, VectorStoreRecordKeyField):
                # Use the property_type directly for key fields
                column_definitions.append(
                    sql.SQL("{} {} PRIMARY KEY").format(sql.Identifier(field_name), sql.SQL(property_type))
                )
            else:
                # Use the property_type directly for other types
                column_definitions.append(sql.SQL("{} {}").format(sql.Identifier(field_name), sql.SQL(property_type)))

        columns_str = sql.SQL(", ").join(column_definitions)

        create_table_query = sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(self.db_schema), sql.Identifier(table_name), columns_str
        )

        async with self.connection_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(create_table_query)
            await conn.commit()

        logger.info(f"Postgres table '{table_name}' created successfully.")

        # If the vector field defines an index, apply it
        for vector_field in self.data_model_definition.vector_fields:
            if vector_field.index_kind:
                await self._create_index(table_name, vector_field)

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
                sql.SQL("CREATE INDEX {} ON {}.{} USING {} ({} {})").format(
                    sql.Identifier(index_name),
                    sql.Identifier(self.db_schema),
                    sql.Identifier(table_name),
                    sql.SQL(vector_field.index_kind),
                    sql.Identifier(column_name),
                    sql.SQL(ops_str),
                )
            )
            await conn.commit()

        logger.info(f"Index '{index_name}' created successfully on column '{column_name}'.")

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
                sql.SQL("DROP TABLE {scm}.{tbl} CASCADE").format(
                    scm=sql.Identifier(self.db_schema), tbl=sql.Identifier(self.collection_name)
                ),
            )
            await conn.commit()
