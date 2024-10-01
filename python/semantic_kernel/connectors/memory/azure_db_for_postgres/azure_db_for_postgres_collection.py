# Copyright (c) Microsoft. All rights reserved.
from typing import TypeVar

from psycopg_pool import AsyncConnectionPool

from semantic_kernel.connectors.memory.azure_db_for_postgres.azure_db_for_postgres_settings import (
    AzureDBForPostgresSettings,
)
from semantic_kernel.connectors.memory.postgres.constants import DEFAULT_SCHEMA
from semantic_kernel.connectors.memory.postgres.postgres_collection import PostgresCollection
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition

TKey = TypeVar("TKey", str, int)
TModel = TypeVar("TModel")


class AzureDBForPostgresCollection(PostgresCollection[TKey, TModel]):
    """AzureDBForPostgresCollection class."""

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        connection_pool: AsyncConnectionPool | None = None,
        db_schema: str = DEFAULT_SCHEMA,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        settings: AzureDBForPostgresSettings | None = None,
    ):
        """Initialize the collection.

        Args:
            collection_name: The name of the collection, which corresponds to the table name.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition: The data model definition.
            connection_pool: The connection pool.
            db_schema: The database schema.
            env_file_path (str): Use the environment settings file as a fallback to environment variables.
            env_file_encoding (str): The encoding of the environment settings file.
            settings: The settings for the Azure DB for Postgres connection. If not provided, the settings will be
                created from the environment.
        """
        # If the connection pool or settings were not provided, create the settings from the environment.
        # Passing this to the super class will enforce using Azure DB settings.
        if not connection_pool and not settings:
            settings = AzureDBForPostgresSettings.create(
                env_file_path=env_file_path, env_file_encoding=env_file_encoding
            )
        super().__init__(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            connection_pool=connection_pool,
            db_schema=db_schema,
            settings=settings,
        )
