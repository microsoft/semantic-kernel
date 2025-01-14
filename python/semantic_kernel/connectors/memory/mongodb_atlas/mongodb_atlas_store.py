# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import TYPE_CHECKING, Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

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

    mongo_client: MongoClient

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
        mongo_client: MongoClient | None = None,
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

        managed_client: bool = False
        if not mongo_client:
            try:
                mongodb_atlas_settings = MongoDBAtlasSettings.create(
                    env_file_path=env_file_path,
                    connection_string=connection_string,
                    database_name=database_name,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as exc:
                raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
            mongo_client = MongoClient(mongodb_atlas_settings.connection_string)
            managed_client = True

        super().__init__(mongo_client=mongo_client, managed_client=managed_client)

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        mongo_client: MongoClient | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a MongoDBAtlasCollection tied to a collection.

        Args:
            collection_name (str): The name of the collection.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            mongo_client (MongoClient | None): The MongoDB client for interacting with MongoDB Atlas,
                will be created if not supplied.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = MongoDBAtlasCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                mongo_client=mongo_client or self.mongo_client,
                collection_name=collection_name,
                managed_client=mongo_client is None,
                **kwargs,
            )
        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        database: Database = self.mongo_client.get_database()
        return await database.list_collection_names()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            self.mongo_client.close()
