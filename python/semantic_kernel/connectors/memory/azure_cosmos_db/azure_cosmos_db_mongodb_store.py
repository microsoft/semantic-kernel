# Copyright (c) Microsoft. All rights reserved.

import sys
from importlib import metadata
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import ValidationError
from pymongo import AsyncMongoClient
from pymongo.driver_info import DriverInfo

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_collection import (
    AzureCosmosDBforMongoDBCollection,
)
from semantic_kernel.connectors.memory.mongodb_atlas.const import DEFAULT_DB_NAME
from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_store import MongoDBAtlasStore
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.exceptions import VectorStoreInitializationException
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if TYPE_CHECKING:
    from semantic_kernel.data.vector_storage import VectorStoreRecordCollection

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

TModel = TypeVar("TModel")


@experimental
class AzureCosmosDBforMongoDBStore(MongoDBAtlasStore):
    """Azure Cosmos DB for MongoDB store implementation."""

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the AzureCosmosDBforMongoDBStore client.

        Args:
        connection_string (str): The connection string for Azure CosmosDB for MongoDB, optional.
            Can be read from environment variables.
        database_name (str): The name of the database, optional. Can be read from environment variables.
        mongo_client (MongoClient): The MongoDB client, optional.
        env_file_path (str): Use the environment settings file as a fallback
            to environment variables.
        env_file_encoding (str): The encoding of the environment settings file.

        """
        managed_client: bool = not mongo_client
        if mongo_client:
            super().__init__(
                mongo_client=mongo_client,
                managed_client=managed_client,
                database_name=database_name or DEFAULT_DB_NAME,
            )
            return
        from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings import (
            AzureCosmosDBforMongoDBSettings,
        )

        try:
            settings = AzureCosmosDBforMongoDBSettings(
                env_file_path=env_file_path,
                connection_string=connection_string,
                database_name=database_name,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
        if not settings.connection_string:
            raise VectorStoreInitializationException("The connection string is missing.")

        mongo_client = AsyncMongoClient(
            settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
        )

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a AzureCosmosDBforMongoDBCollection tied to a collection.

        Args:
            collection_name (str): The name of the collection.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = AzureCosmosDBforMongoDBCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                mongo_client=self.mongo_client,
                collection_name=collection_name,
                database_name=self.database_name,
                **kwargs,
            )
        return self.vector_record_collections[collection_name]
