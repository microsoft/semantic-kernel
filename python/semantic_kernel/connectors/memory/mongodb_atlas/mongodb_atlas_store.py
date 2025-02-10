# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from importlib import metadata
from typing import TYPE_CHECKING, Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.driver_info import DriverInfo

from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_collection import (
    MongoDBAtlasCollection,
)
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage import VectorStore
from semantic_kernel.exceptions import VectorStoreInitializationException
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data import VectorStoreRecordCollection


logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class MongoDBAtlasStore(VectorStore):
    """MongoDB Atlas store implementation."""

    mongo_client: AsyncMongoClient
    database_name: str

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the MongoDBAtlasStore client.

        Args:
        connection_string (str): The connection string for MongoDB Atlas, optional.
            Can be read from environment variables.
        database_name (str): The name of the database, optional. Can be read from environment variables.
        mongo_client (MongoClient): The MongoDB client, optional.
        env_file_path (str): Use the environment settings file as a fallback
            to environment variables.
        env_file_encoding (str): The encoding of the environment settings file.

        """
        from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_settings import (
            MongoDBAtlasSettings,
        )

        if mongo_client and database_name:
            super().__init__(
                mongo_client=mongo_client,
                managed_client=False,
                database_name=database_name,
            )
        managed_client: bool = False
        try:
            mongodb_atlas_settings = MongoDBAtlasSettings.create(
                env_file_path=env_file_path,
                connection_string=connection_string,
                database_name=database_name,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
        if not mongo_client:
            mongo_client = AsyncMongoClient(
                mongodb_atlas_settings.connection_string.get_secret_value(),
                driver=DriverInfo("Microsoft Semantic Kernel", metadata.version("semantic-kernel")),
            )
            managed_client = True

        super().__init__(
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=mongodb_atlas_settings.database_name,
        )

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a MongoDBAtlasCollection tied to a collection.

        Args:
            collection_name (str): The name of the collection.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = MongoDBAtlasCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                mongo_client=self.mongo_client,
                collection_name=collection_name,
                database_name=self.database_name,
                **kwargs,
            )
        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        database: AsyncDatabase = self.mongo_client.get_database(self.database_name)
        return await database.list_collection_names()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.mongo_client.close()

    async def __aenter__(self) -> "MongoDBAtlasStore":
        """Enter the context manager."""
        await self.mongo_client.aconnect()
        return self
