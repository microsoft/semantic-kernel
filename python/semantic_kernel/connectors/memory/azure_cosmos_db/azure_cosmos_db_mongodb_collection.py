# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable
from importlib import metadata
from typing import Any, Generic

from pydantic import ValidationError
from pymongo import AsyncMongoClient
from pymongo.driver_info import DriverInfo

from semantic_kernel.connectors.memory.azure_cosmos_db.const import (
    DISTANCE_FUNCTION_MAPPING_MONGODB,
    INDEX_KIND_MAPPING_MONGODB,
)
from semantic_kernel.connectors.memory.mongodb_atlas.const import (
    DEFAULT_DB_NAME,
    MONGODB_SCORE_FIELD,
)
from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_collection import MongoDBAtlasCollection
from semantic_kernel.data.record_definition import VectorStoreRecordDataField, VectorStoreRecordDefinition
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import VectorSearchOptions, VectorSearchResult
from semantic_kernel.data.vector_storage import TKey, TModel
from semantic_kernel.exceptions import (
    VectorStoreInitializationException,
)
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorSearchExecutionException,
    VectorStoreModelDeserializationException,
)
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AzureCosmosDBforMongoDBCollection(MongoDBAtlasCollection[TKey, TModel], Generic[TKey, TModel]):
    """Azure Cosmos DB for MongoDB collection."""

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        mongo_client: AsyncMongoClient | None = None,
        connection_string: str | None = None,
        database_name: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the AzureCosmosDBforMongoDBCollection class.

        Args:
            data_model_type: The type of the data model.
            data_model_definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            mongo_client: The MongoDB client for interacting with Azure CosmosDB for MongoDB,
                used for creating and deleting collections.
            connection_string: The connection string for MongoDB Atlas, optional.
            Can be read from environment variables.
            database_name: The name of the database, will be filled from the env when this is not set.
            connection_string: str | None = None,
            env_file_path: str | None = None,
            env_file_encoding: str | None = None
            **kwargs: Additional keyword arguments

        """
        managed_client = not mongo_client
        if mongo_client:
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                mongo_client=mongo_client,
                collection_name=collection_name,
                database_name=database_name or DEFAULT_DB_NAME,
                managed_client=managed_client,
            )
            return

        from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings import (
            AzureCosmosDBforMongoDBSettings,
        )

        try:
            settings = AzureCosmosDBforMongoDBSettings(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                connection_string=connection_string,
                database_name=database_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create Azure CosmosDB for MongoDB settings.") from exc
        if not settings.connection_string:
            raise VectorStoreInitializationException("The Azure CosmosDB for MongoDB connection string is required.")

        mongo_client = AsyncMongoClient(
            settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
        )

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in Azure CosmosDB for MongoDB.

        This first creates a collection, with the kwargs.
        Then creates a search index based on the data model definition.

        By the naming convection of MongoDB indexes are created by using the field name
        with a underscore.

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
        indexes = [
            {"name": f"{field.name}_", "key": {field.name: 1}}
            for field in self.data_model_definition.fields.values()
            if isinstance(field, VectorStoreRecordDataField) and (field.is_filterable or field.is_full_text_searchable)
        ]
        for vector_field in self.data_model_definition.vector_fields:
            index_name = f"{vector_field.name}_"

            similarity = (
                DISTANCE_FUNCTION_MAPPING_MONGODB.get(vector_field.distance_function)
                if vector_field.distance_function
                else "COS"
            )
            kind = INDEX_KIND_MAPPING_MONGODB.get(vector_field.index_kind) if vector_field.index_kind else "vector-ivf"
            if similarity is None:
                raise VectorStoreInitializationException(f"Invalid distance function: {vector_field.distance_function}")
            if kind is None:
                raise VectorStoreInitializationException(f"Invalid index kind: {vector_field.index_kind}")
            index: dict[str, Any] = {
                "name": index_name,
                "key": {vector_field.name: "cosmosSearch"},
                "cosmosSearchOptions": {
                    "kind": kind,
                    "similarity": similarity,
                    "dimensions": vector_field.dimensions,
                },
            }
            match kind:
                case "vector-diskann":
                    if "maxDegree" in kwargs:
                        index["cosmosSearchOptions"]["maxDegree"] = kwargs["maxDegree"]
                    if "lBuild" in kwargs:
                        index["cosmosSearchOptions"]["lBuild"] = kwargs["lBuild"]
                case "vector-hnsw":
                    if "m" in kwargs:
                        index["cosmosSearchOptions"]["m"] = kwargs["m"]
                    if "efConstruction" in kwargs:
                        index["cosmosSearchOptions"]["efConstruction"] = kwargs["efConstruction"]
                case "vector-ivf":
                    if "numList" in kwargs:
                        index["cosmosSearchOptions"]["numList"] = kwargs["numList"]
            indexes.append(index)

        return {"createIndexes": self.collection_name, "indexes": indexes}

    @override
    async def _inner_vectorized_search(
        self,
        options: VectorSearchOptions,
        vector: list[float | int],
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        vector_search_query: dict[str, Any] = {
            "k": options.top + options.skip,
            "index": f"{options.vector_field_name}_",
            "vector": vector,
            "path": options.vector_field_name,
        }
        if options.filter.filters:
            vector_search_query["filter"] = self._build_filter_dict(options.filter)
        projection_query: dict[str, int | dict] = {
            field: 1
            for field in self.data_model_definition.get_field_names(
                include_vector_fields=options.include_vectors,
                include_key_field=False,  # _id is always included
            )
        }
        projection_query[MONGODB_SCORE_FIELD] = {"$meta": "searchScore"}
        try:
            raw_results = await collection.aggregate([
                {"$search": {"cosmosSearch": vector_search_query}},
                {"$project": projection_query},
            ])
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search the collection.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results, options),
            total_count=None,  # no way to get a count before looping through the result cursor
        )

    async def _get_vector_search_results_from_cursor(
        self,
        filter: dict[str, Any],
        projection: dict[str, int | dict],
        options: VectorSearchOptions | None = None,
    ) -> AsyncIterable[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        async for result in collection.find(
            filter=filter,
            projection=projection,
            skip=options.skip if options else 0,
            limit=options.top if options else 0,
        ):
            try:
                record = self.deserialize(
                    self._get_record_from_result(result), include_vectors=options.include_vectors if options else True
                )
            except VectorStoreModelDeserializationException:
                raise
            except Exception as exc:
                raise VectorStoreModelDeserializationException(
                    f"An error occurred while deserializing the record: {exc}"
                ) from exc
            score = self._get_score_from_result(result)
            if record:
                # single records are always returned as single records by the deserializer
                yield VectorSearchResult(record=record, score=score)  # type: ignore
