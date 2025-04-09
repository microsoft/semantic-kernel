# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, TypeVar

from psycopg import sql
from psycopg_pool import AsyncConnectionPool

from semantic_kernel.connectors.memory.postgres.postgres_collection import PostgresCollection
from semantic_kernel.connectors.memory.postgres.postgres_memory_store import DEFAULT_SCHEMA
from semantic_kernel.data import VectorStore, VectorStoreRecordCollection, VectorStoreRecordDefinition
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental
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
                # data model definition will be validated in the collection
                data_model_definition=data_model_definition,  # type: ignore
                **kwargs,
            )

        return self.vector_record_collections[collection_name]
