# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Generic, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pydantic import ValidationError

from semantic_kernel.data.filter_clauses import AnyTagsEqualTo, EqualTo
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition, VectorStoreRecordVectorField
from semantic_kernel.data.vector_search import (
    VectorizableTextSearchMixin,
    VectorSearchFilter,
    VectorSearchOptions,
)
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vector_text_search import VectorTextSearchMixin
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
    VectorizableTextSearchMixin[TModel],
    VectorizedSearchMixin[TModel],
    VectorTextSearchMixin[TModel],
    Generic[TModel],
):
    """MongoDB Atlas collection implementation."""

    mongo_client: MongoClient
    supported_key_types: ClassVar[list[str] | None] = ["str"]
    supported_vector_types: ClassVar[list[str] | None] = ["float", "int"]
    managed_mongo_client: bool = True

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        mongo_client: MongoClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the MongoDBAtlasCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition): The model definition, optional.
            collection_name (str): The name of the collection, optional.
            mongo_client (MongoClient): The MongoDB client for interacting with MongoDB Atlas,
                used for creating and deleting collections.
            **kwargs: Additional keyword arguments, including:
                The same keyword arguments used for MongoDBAtlasStore:
                    connection_string: str | None = None,
                    database_name: str | None = None,
                    env_file_path: str | None = None,
                    env_file_encoding: str | None = None

        """
        if mongo_client:
            if not collection_name:
                raise VectorStoreInitializationException("Collection name is required.")
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                mongo_client=mongo_client,
                managed_mongo_client=False,
            )
            return

        from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_settings import (
            MongoDBAtlasSettings,
        )

        try:
            mongodb_atlas_settings = MongoDBAtlasSettings.create(
                env_file_path=kwargs.get("env_file_path"),
                connection_string=kwargs.get("connection_string"),
                database_name=kwargs.get("database_name"),
                env_file_encoding=kwargs.get("env_file_encoding"),
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
        mongo_client = MongoClient(mongodb_atlas_settings.connection_string)
        if not mongodb_atlas_settings.database_name:
            raise VectorStoreInitializationException("Database name is required.")

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=mongodb_atlas_settings.database_name,
            mongo_client=mongo_client,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[str]:
        if not isinstance(records, list):
            records = list(records)
        collection: Collection = self.mongo_client.get_database().get_collection(self.collection_name)
        result = await collection.insert_many(records, **kwargs)
        return [str(inserted_id) for inserted_id in result.inserted_ids]

    @override
    async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Sequence[dict[str, Any]]:
        collection: Collection = self.mongo_client.get_database().get_collection(self.collection_name)
        result = await asyncio.gather(
            *[collection.find_one({"_id": key}) for key in keys],
            return_exceptions=True,
        )
        return [res for res in result if not isinstance(res, BaseException)]

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        collection: Collection = self.mongo_client.get_database().get_collection(self.collection_name)
        await collection.delete_many({"_id": {"$in": keys}})

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        return records

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return records

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in MongoDB Atlas.

        Args:
            **kwargs: Additional keyword arguments.
        """
        database: Database = self.mongo_client.get_database()
        await database.create_collection(self.collection_name, **kwargs)

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        database: Database = self.mongo_client.get_database()
        return self.collection_name in await database.list_collection_names()

    @override
    async def delete_collection(self, **kwargs) -> None:
        database: Database = self.mongo_client.get_database()
        await database.drop_collection(self.collection_name, **kwargs)

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection: Collection = self.mongo_client.get_database().get_collection(self.collection_name)
        search_args: dict[str, Any] = {
            "limit": options.top,
            "skip": options.skip,
        }
        if options.filter.filters:
            search_args["filter"] = self._build_filter_dict(options.filter)
        if vector is not None:
            search_args["vector"] = vector
        if "vector" not in search_args:
            raise VectorStoreOperationException("Vector is required for search.")

        try:
            raw_results = await collection.find(search_args)
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search the collection.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results, options),
            total_count=await raw_results.count() if options.include_total_count else None,
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
        if self.managed_mongo_client:
            self.mongo_client.close()
