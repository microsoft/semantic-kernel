# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, TypeVar

from pydantic import ValidationError

from semantic_kernel.connectors.memory.postgres.postgres_collection import PostgresCollection
from semantic_kernel.connectors.memory.postgres.postgres_memory_store import DEFAULT_SCHEMA
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings
from semantic_kernel.connectors.memory.postgres.utils import ConnectionPoolWrapper
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from psycopg_pool import ConnectionPool

from semantic_kernel.data.vector_store import VectorStore
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class PostgresStore(VectorStore):
    """PostgreSQL store implementation."""

    connection_pool: ConnectionPool
    db_schema: str = DEFAULT_SCHEMA
    tables: list[str] | None = None
    """Tables to consider as collections. Default is all tables in the schema."""

    def __init__(
        self,
        db_schema: str = DEFAULT_SCHEMA,
        tables: list[str] | None = None,
        connection_pool: ConnectionPool | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the PostgresStore.

        Args:
            db_schema: The schema to consider as the store.
            tables: The tables to consider as collections. Default is all tables in the schema.
            connection_pool: Optional connection pool. If not supplied, one will be created from settings.
                All collections will share the same connection pool. If not supplied, the created
                connection pool will be closed when __del__ is called on this object.
            env_file_path (str): Use the environment settings file as a fallback to environment variables.
            env_file_encoding (str): The encoding of the environment settings file.
            **kwargs: Additional keyword arguments passed to the client constructor.
        """
        try:
            settings = PostgresSettings.create(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise MemoryConnectorInitializationError("Failed to create Postgres settings.", e) from e

        if not connection_pool:
            connection_pool = ConnectionPoolWrapper(
                min_size=settings.min_pool,
                max_size=settings.max_pool,
                open=False,
                kwargs=settings.get_connection_args(),
            )
            connection_pool.open()

        super().__init__(connection_pool=connection_pool, schema=db_schema, tables=tables, **kwargs)

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        with self.connection_pool.connection() as conn, conn.cursor() as cur:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                """
            params = (self.db_schema,)

            if self.tables:
                query += f" AND table_name IN ({', '.join(['%s'] * len(self.tables))})"
                params += tuple(self.tables)

            cur.execute(query, params)
            return [row[0] for row in cur.fetchall()]

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> VectorStoreRecordCollection:
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = PostgresCollection(
                connection_pool=self.connection_pool,
                db_schema=self.db_schema,
                collection_name=collection_name,
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                **kwargs,
            )

        return self.vector_record_collections[collection_name]
