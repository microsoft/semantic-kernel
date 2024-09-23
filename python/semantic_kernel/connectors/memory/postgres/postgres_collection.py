# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, TypeVar

from semantic_kernel.connectors.memory.postgres.utils import convert_row_to_dict, python_type_to_postgres

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from psycopg import sql
from psycopg.errors import DatabaseError
from psycopg_pool import ConnectionPool

from semantic_kernel.connectors.memory.postgres.constants import MAX_DIMENSIONALITY, MAX_KEYS_PER_BATCH
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordKeyField, VectorStoreRecordVectorField
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    VectorStoreModelValidationError,
)
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TKey = TypeVar("TKey", str, int)
TModel = TypeVar("TModel")

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class PostgresCollection(VectorStoreRecordCollection[TKey, TModel]):
    """PostgreSQL collection implementation."""

    connection_pool: ConnectionPool
    db_schema: str
    supported_key_types: ClassVar[list[str] | None] = ["str", "int"]
    supported_vector_types: ClassVar[list[str] | None] = ["float"]

    @override
    def _validate_data_model(self) -> None:
        """Validate the data model."""

        def _check_dimensionality(dimension_num):
            if dimension_num > MAX_DIMENSIONALITY:
                raise VectorStoreModelValidationError(
                    f"Dimensionality of {dimension_num} exceeds the maximum allowed value of {MAX_DIMENSIONALITY}."
                )
            if dimension_num <= 0:
                raise VectorStoreModelValidationError("Dimensionality must be a positive integer. ")

        for field in self.data_model_definition.vector_fields:
            if field.dimensions:
                _check_dimensionality(field.dimensions)

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
            **kwargs (Any): Additional arguments, to be passed to the store.

        Returns:
            The keys of the upserted records.
        """
        keys = []
        try:
            with self.connection_pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
                # Split the records into batches
                for i in range(0, len(records), MAX_KEYS_PER_BATCH):
                    record_batch = records[i : i + MAX_KEYS_PER_BATCH]

                    # Execute the INSERT statement for each batch
                    cur.executemany(
                        sql.SQL("INSERT INTO {}.{} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}").format(
                            sql.Identifier(self.db_schema),
                            sql.Identifier(self.collection_name),
                            sql.SQL(", ").join(
                                sql.Identifier(field.name) for field in self.data_model_definition.fields.values()
                            ),
                            sql.SQL(", ").join(sql.Placeholder() * len(self.data_model_definition.fields)),
                            sql.Identifier(self.data_model_definition.key_field.name),
                            sql.SQL(", ").join(
                                sql.SQL("{field} = EXCLUDED.{field}").format(field=sql.Identifier(field.name))
                                for field in self.data_model_definition.fields.values()
                                if field.name != self.data_model_definition.key_field.name
                            ),
                        ),
                        [
                            tuple(record.get(field.name) for field in self.data_model_definition.fields.values())
                            for record in record_batch
                        ],
                    )
                    keys.extend(record.get(self.data_model_definition.key_field.name) for record in record_batch)
            # Commit transaction after all batches succeed
            conn.commit()
        except DatabaseError as error:
            # Rollback happens automatically if an exception occurs within the transaction block
            raise MemoryConnectorException(f"Error upserting records: {error}") from error

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
        fields = [(field.name, field) for field in self.data_model_definition.fields.values()]
        try:
            with self.connection_pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT {} FROM {}.{} WHERE {} IN ({})").format(
                        sql.SQL(", ").join(sql.Identifier(name) for (name, _) in fields),
                        sql.Identifier(self.db_schema),
                        sql.Identifier(self.collection_name),
                        sql.Identifier(self.data_model_definition.key_field.name),
                        sql.SQL(", ").join(sql.Literal(key) for key in keys),
                    )
                )
                rows = cur.fetchall()
                if not rows:
                    return None
                if len(rows) == 1:
                    return convert_row_to_dict(rows[0], fields)
                return [convert_row_to_dict(row, fields) for row in rows]

        except DatabaseError as error:
            raise MemoryConnectorException(f"Error getting records: {error}") from error

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records with the given keys.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.
        """
        try:
            with self.connection_pool.connection() as conn, conn.transaction():
                with conn.cursor() as cur:
                    # Split the keys into batches
                    for i in range(0, len(keys), MAX_KEYS_PER_BATCH):
                        key_batch = keys[i : i + MAX_KEYS_PER_BATCH]

                        # Execute the DELETE statement for each batch
                        cur.execute(
                            sql.SQL("DELETE FROM {}.{} WHERE {} IN ({})").format(
                                sql.Identifier(self.db_schema),
                                sql.Identifier(self.collection_name),
                                sql.Identifier(self.data_model_definition.key_field.name),
                                sql.SQL(", ").join(sql.Literal(key) for key in key_batch),
                            )
                        )
                # Commit transaction after all batches succeed
                conn.commit()
        except DatabaseError as error:
            # Rollback happens automatically if an exception occurs within the transaction block
            raise MemoryConnectorException(f"Error deleting records: {error}") from error

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

        :param table_name: Name of the table to be created
        :param fields: A dictionary where keys are column names and values are VectorStoreRecordField instances
        """
        column_definitions = []
        table_name = self.collection_name

        for field_name, field in self.data_model_definition.fields.items():
            if not field.property_type:
                raise ValueError(f"Property type is not defined for field '{field_name}'")

            # If the property type represents a Python type, convert it to a PostgreSQL type
            property_type = python_type_to_postgres(field.property_type) or field.property_type.upper()

            # For Vector fields with dimensions, use pgvector's VECTOR type
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

        # Create the final CREATE TABLE statement
        create_table_query = sql.SQL("CREATE TABLE {}.{} ({})").format(
            sql.Identifier(self.db_schema), sql.Identifier(table_name), columns_str
        )

        try:
            # Establish the database connection using psycopg3
            with self.connection_pool.connection() as conn, conn.cursor() as cur:
                # Execute the CREATE TABLE query
                cur.execute(create_table_query)
                conn.commit()

            logger.info(f"Postgres table '{table_name}' created successfully.")

        except DatabaseError as error:
            raise MemoryConnectorException(f"Error creating table: {error}") from error

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        with self.connection_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                """,
                (self.db_schema, self.collection_name),
            )
            return bool(cur.fetchone())

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection."""
        with self.connection_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                sql.SQL("DROP TABLE {scm}.{tbl} CASCADE").format(
                    scm=sql.Identifier(self.db_schema), tbl=sql.Identifier(self.collection_name)
                ),
            )
