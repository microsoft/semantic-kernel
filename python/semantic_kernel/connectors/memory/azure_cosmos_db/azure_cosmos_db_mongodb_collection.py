# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from importlib import metadata
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError
from pymongo import AsyncMongoClient
from pymongo.driver_info import DriverInfo

from semantic_kernel.connectors.memory.azure_cosmos_db.const import (
    DISTANCE_FUNCTION_MAPPING_MONGODB,
    INDEX_KIND_MAPPING_MONGODB,
)
from semantic_kernel.connectors.memory.mongodb_atlas.const import (
    DEFAULT_DB_NAME,
    DEFAULT_SEARCH_INDEX_NAME,
)
from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_collection import MongoDBAtlasCollection
from semantic_kernel.data.const import IndexKind
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.exceptions import (
    VectorStoreInitializationException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class AzureCosmosDBforMongoDBCollection(MongoDBAtlasCollection):
    """Azure Cosmos DB for MongoDB collection."""

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        index_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the AzureCosmosDBforMongoDBCollection class.

        Args:
            data_model_type: The type of the data model.
            data_model_definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            mongo_client: The MongoDB client for interacting with Azure CosmosDB for MongoDB,
                used for creating and deleting collections.
            index_name: The name of the index to use for searching, when not passed, will use <collection_name>_idx.
            **kwargs: Additional keyword arguments, including:
                The same keyword arguments used for AzureCosmosDBforMongoDBStore:
                    database_name: The name of the database, will be filled from the env when this is not set.
                    connection_string: str | None = None,
                    env_file_path: str | None = None,
                    env_file_encoding: str | None = None

        """
        managed_client = not mongo_client
        if mongo_client:
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                mongo_client=mongo_client,
                collection_name=collection_name,
                database_name=kwargs.get("database_name", DEFAULT_DB_NAME),
                index_name=index_name or DEFAULT_SEARCH_INDEX_NAME,
                managed_client=managed_client,
            )
            return

        from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings import (
            AzureCosmosDBforMongoDBSettings,
        )

        try:
            settings = AzureCosmosDBforMongoDBSettings.create(
                env_file_path=kwargs.get("env_file_path"),
                env_file_encoding=kwargs.get("env_file_encoding"),
                connection_string=kwargs.get("connection_string"),
                database_name=kwargs.get("database_name"),
                index_name=index_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create Azure CosmosDB for MongoDB settings.") from exc
        if not mongo_client:
            mongo_client = AsyncMongoClient(
                settings.connection_string.get_secret_value(),
                driver=DriverInfo("Microsoft Semantic Kernel", metadata.version("semantic-kernel")),
            )

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
            index_name=settings.index_name,
        )

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in Azure CosmosDB for MongoDB.

        This first creates a collection, with the kwargs.
        Then creates a search index based on the data model definition.

        Args:
            **kwargs: Additional keyword arguments.
                These are the additional keyword arguments for creating
                vector indexes in Azure Cosmos DB for MongoDB.
                And they depend on the kind of index you are creating.
                See https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search
                for more information.
                Other kwargs are passed to the create_collection method.
        """
        await self._get_database().create_collection(self.collection_name, **kwargs)
        await self._get_database().command(command=self._get_vector_index(**kwargs))

    def _get_vector_index(self, **kwargs: Any) -> dict[str, Any]:
        indexes = []
        for vector_field in self.data_model_definition.vector_fields:
            index_name = f"{vector_field.name}_"
            similarity = DISTANCE_FUNCTION_MAPPING_MONGODB.get(vector_field.distance_function)
            kind = INDEX_KIND_MAPPING_MONGODB.get(vector_field.index_kind)
            if similarity is None:
                raise VectorStoreInitializationException(f"Invalid distance function: {vector_field.distance_function}")
            if kind is None:
                raise VectorStoreInitializationException(f"Invalid index kind: {vector_field.index_kind}")
            index = {
                "name": index_name,
                "key": {vector_field.name: "cosmosSearch"},
                "cosmosSearchOptions": {
                    "kind": kind,
                    "similarity": similarity,
                    "dimensions": vector_field.dimensions,
                },
            }
            match vector_field.index_kind:
                case IndexKind.DISK_ANN:
                    if "maxDegree" in kwargs:
                        index["cosmosSearchOptions"]["maxDegree"] = kwargs["maxDegree"]
                    if "lBuild" in kwargs:
                        index["cosmosSearchOptions"]["lBuild"] = kwargs["lBuild"]
                case IndexKind.HNSW:
                    if "m" in kwargs:
                        index["cosmosSearchOptions"]["m"] = kwargs["m"]
                    if "efConstruction" in kwargs:
                        index["cosmosSearchOptions"]["efConstruction"] = kwargs["efConstruction"]
                case IndexKind.IVF_FLAT:
                    if "numList" in kwargs:
                        index["cosmosSearchOptions"]["numList"] = kwargs["numList"]
            indexes.append(index)

        return {"createIndexes": self.collection_name, "indexes": indexes}
