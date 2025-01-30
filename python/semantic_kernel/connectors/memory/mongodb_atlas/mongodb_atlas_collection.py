# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from importlib import metadata
from typing import Any, ClassVar, Generic, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.driver_info import DriverInfo

from semantic_kernel.connectors.memory.mongodb_atlas.const import (
    DEFAULT_DB_NAME,
    DEFAULT_SEARCH_INDEX_NAME,
    MONGODB_ID_FIELD,
)
from semantic_kernel.connectors.memory.mongodb_atlas.utils import create_index_definition
from semantic_kernel.data.filter_clauses import AnyTagsEqualTo, EqualTo
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_search import (
    VectorSearchFilter,
    VectorSearchOptions,
)
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class MongoDBAtlasCollection(
    VectorSearchBase[str, TModel],
    VectorizedSearchMixin[TModel],
    Generic[TModel],
):
    """MongoDB Atlas collection implementation."""

    mongo_client: AsyncMongoClient
    database_name: str
    index_name: str
    supported_key_types: ClassVar[list[str] | None] = ["str"]
    supported_vector_types: ClassVar[list[str] | None] = ["float", "int"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        index_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the MongoDBAtlasCollection class.

        Args:
            data_model_type: The type of the data model.
            data_model_definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            mongo_client: The MongoDB client for interacting with MongoDB Atlas,
                used for creating and deleting collections.
            index_name: The name of the index to use for searching, when not passed, will use <collection_name>_idx.
            **kwargs: Additional keyword arguments, including:
                The same keyword arguments used for MongoDBAtlasStore:
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

        from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_settings import MongoDBAtlasSettings

        try:
            mongodb_atlas_settings = MongoDBAtlasSettings.create(
                env_file_path=kwargs.get("env_file_path"),
                env_file_encoding=kwargs.get("env_file_encoding"),
                connection_string=kwargs.get("connection_string"),
                database_name=kwargs.get("database_name"),
                index_name=index_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
        if not mongo_client:
            mongo_client = AsyncMongoClient(
                mongodb_atlas_settings.connection_string.get_secret_value(),
                driver=DriverInfo("Microsoft Semantic Kernel", metadata.version("semantic-kernel")),
            )

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=mongodb_atlas_settings.database_name,
            index_name=mongodb_atlas_settings.index_name,
        )

    def _get_database(self) -> AsyncDatabase:
        """Get the database.

        If you need control over things like read preference, you can override this method.
        """
        return self.mongo_client.get_database(self.database_name)

    def _get_collection(self) -> AsyncCollection:
        """Get the collection.

        If you need control over things like read preference, you can override this method.
        """
        return self.mongo_client.get_database(self.database_name).get_collection(self.collection_name)

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[str]:
        result = await self._get_collection().update_many(update=records, upsert=True, **kwargs)
        return [str(ids) for ids in result.upserted_id]

    @override
    async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Sequence[dict[str, Any]]:
        result = self._get_collection().find({MONGODB_ID_FIELD: {"$in": keys}})
        return await result.to_list(length=len(keys))

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        collection = self._get_collection()
        await collection.delete_many({MONGODB_ID_FIELD: {"$in": keys}})

    def _replace_key_field(self, record: dict[str, Any]) -> dict[str, Any]:
        if self._key_field_name == MONGODB_ID_FIELD:
            return record
        return {
            MONGODB_ID_FIELD: record.pop(self._key_field_name, None),
            **record,
        }

    def _reset_key_field(self, record: dict[str, Any]) -> dict[str, Any]:
        if self._key_field_name == MONGODB_ID_FIELD:
            return record
        return {
            self._key_field_name: record.pop(MONGODB_ID_FIELD, None),
            **record,
        }

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        return [self._replace_key_field(record) for record in records]

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return [self._reset_key_field(record) for record in records]

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in MongoDB Atlas.

        This first creates a collection, with the kwargs.
        Then creates a search index based on the data model definition.

        Args:
            **kwargs: Additional keyword arguments.
        """
        collection = await self._get_database().create_collection(self.collection_name, **kwargs)
        await collection.create_search_index(create_index_definition(self.data_model_definition, self.index_name))

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        return bool(await self._get_database().list_collection_names(filter={"name": self.collection_name}))

    @override
    async def delete_collection(self, **kwargs) -> None:
        await self._get_database().drop_collection(self.collection_name, **kwargs)

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        vector_search_query: dict[str, Any] = {
            "limit": options.top + options.skip,
            "index": self.index_name,
        }
        if options.filter.filters:
            vector_search_query["filter"] = self._build_filter_dict(options.filter)
        if vector is not None:
            vector_search_query["queryVector"] = vector
            vector_search_query["path"] = options.vector_field_name
        if "queryVector" not in vector_search_query:
            raise VectorStoreOperationException("Vector is required for search.")

        projection_query: dict[str, int | dict] = {
            field: 1
            for field in self.data_model_definition.get_field_names(
                include_vector_fields=options.include_vectors,
                include_key_field=False,  # _id is always included
            )
        }
        projection_query["score"] = {"$meta": "vectorSearchScore"}
        try:
            raw_results = await collection.aggregate([
                {"$vectorSearch": vector_search_query},
                {"$project": projection_query},
            ])
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search the collection.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results, options),
            total_count=None,  # no way to get a count before looping through the result cursor
        )

    def _build_filter_dict(self, search_filter: VectorSearchFilter) -> dict[str, Any]:
        """Create the filter dictionary based on the filters."""
        filter_dict = {}
        for filter in search_filter.filters:
            if isinstance(filter, EqualTo):
                filter_dict[filter.field_name] = filter.value
            elif isinstance(filter, AnyTagsEqualTo):
                filter_dict[filter.field_name] = {"$in": filter.value}
        return filter_dict

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get("score")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.mongo_client.close()

    async def __aenter__(self) -> "MongoDBAtlasCollection":
        """Enter the context manager."""
        await self.mongo_client.aconnect()
        return self
