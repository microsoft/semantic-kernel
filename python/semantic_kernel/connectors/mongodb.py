# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import MutableSequence, Sequence
from importlib import metadata
from typing import Any, ClassVar, Final, Generic, TypeVar

from pydantic import SecretStr, ValidationError
from pymongo import AsyncMongoClient, ReplaceOne
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.driver_info import DriverInfo
from pymongo.operations import SearchIndexModel

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DistanceFunction,
    GetFilteredRecordOptions,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    VectorStoreField,
    _get_collection_name_from_model,
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreModelException
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override


TKey = TypeVar("TKey", bound=str)

DEFAULT_DB_NAME: Final[str] = "default"
DEFAULT_SEARCH_INDEX_NAME: Final[str] = "default"
MONGODB_ID_FIELD: Final[str] = "_id"
MONGODB_SCORE_FIELD: Final[str] = "score"
NUM_CANDIDATES_SCALAR: Final[int] = 10
DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.DOT_PROD: "dotProduct",
    DistanceFunction.DEFAULT: "euclidean",
}

logger = logging.getLogger(__name__)


@release_candidate
class MongoDBAtlasSettings(KernelBaseSettings):
    """MongoDB Atlas model settings.

    Args:
    - connection_string: str - MongoDB Atlas connection string
        (Env var MONGODB_ATLAS_CONNECTION_STRING)
    - database_name: str - MongoDB Atlas database name, defaults to 'default'
        (Env var MONGODB_ATLAS_DATABASE_NAME)
    - index_name: str - MongoDB Atlas search index name, defaults to 'default'
        (Env var MONGODB_ATLAS_INDEX_NAME)
    """

    env_prefix: ClassVar[str] = "MONGODB_ATLAS_"

    connection_string: SecretStr
    database_name: str = DEFAULT_DB_NAME
    index_name: str = DEFAULT_SEARCH_INDEX_NAME


def _create_vector_field(field: VectorStoreField) -> dict:
    """Create a vector field.

    Args:
        field (VectorStoreRecordVectorField): The vector field.

    Returns:
        dict: The vector field.
    """
    if field.distance_function not in DISTANCE_FUNCTION_MAP:
        raise VectorStoreInitializationException(
            f"Distance function {field.distance_function} is not supported. "
            f"Supported distance functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
        )
    return {
        "type": "vector",
        "numDimensions": field.dimensions,
        "path": field.storage_name or field.name,
        "similarity": DISTANCE_FUNCTION_MAP[field.distance_function],
    }


def _create_index_definitions(
    record_definition: VectorStoreCollectionDefinition, index_name: str
) -> list[SearchIndexModel]:
    """Create the index definitions."""
    indexes = []
    if record_definition.vector_fields:
        vector_fields = [_create_vector_field(field) for field in record_definition.vector_fields]
        filterable_fields = [
            {"path": field.storage_name or field.name, "type": "filter"}
            for field in record_definition.data_fields
            if field.is_indexed
        ]
        filterable_fields.append({"path": record_definition.key_field.name, "type": "filter"})
        indexes.append(
            SearchIndexModel(
                type="vectorSearch",
                name=index_name,
                definition={"fields": vector_fields + filterable_fields},
            )
        )
    if record_definition.data_fields:
        ft_indexed_fields = [
            {field.storage_name or field.name: {"type": "string"}}
            for field in record_definition.data_fields
            if field.is_full_text_indexed
        ]
        if ft_indexed_fields:
            indexes.append(
                SearchIndexModel(
                    type="search",
                    name=f"{index_name}_ft",
                    definition={
                        "mapping": {"dynamic": True, "fields": ft_indexed_fields},
                    },
                )
            )
    return indexes


@release_candidate
class MongoDBAtlasCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """MongoDB Atlas collection implementation."""

    mongo_client: AsyncMongoClient
    database_name: str
    index_name: str
    supported_key_types: ClassVar[set[str] | None] = {"str"}
    supported_vector_types: ClassVar[set[str] | None] = {"float", "int"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR, SearchType.KEYWORD_HYBRID}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        index_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        connection_string: str | None = None,
        database_name: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the MongoDBAtlasCollection class.

        Args:
            record_type: The type of the data model.
            definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            embedding_generator: The embedding generator, optional.
            index_name: The name of the index to use for searching, when not passed, will use <collection_name>_idx.
            mongo_client: The MongoDB client for interacting with MongoDB Atlas,
                used for creating and deleting collections.
            connection_string: The connection string for MongoDB Atlas, optional.
            Can be read from environment variables.
            database_name: The name of the database, will be filled from the env when this is not set.
            connection_string: str | None = None,
            env_file_path: str | None = None,
            env_file_encoding: str | None = None
            **kwargs: Additional keyword arguments
        """
        if not collection_name:
            collection_name = _get_collection_name_from_model(record_type, definition)
        managed_client = kwargs.get("managed_client", not mongo_client)
        if mongo_client:
            super().__init__(
                record_type=record_type,
                definition=definition,
                mongo_client=mongo_client,
                collection_name=collection_name,
                database_name=database_name or DEFAULT_DB_NAME,
                index_name=index_name or DEFAULT_SEARCH_INDEX_NAME,
                managed_client=managed_client,
                embedding_generator=embedding_generator,
            )
            return

        try:
            mongodb_atlas_settings = MongoDBAtlasSettings(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                connection_string=connection_string,
                database_name=database_name,
                index_name=index_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc

        mongo_client = AsyncMongoClient(
            mongodb_atlas_settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=mongodb_atlas_settings.database_name,
            index_name=mongodb_atlas_settings.index_name,
            embedding_generator=embedding_generator,
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
    ) -> Sequence[TKey]:
        operations: MutableSequence[ReplaceOne] = []
        for record in records:
            operations.append(
                ReplaceOne(
                    filter={MONGODB_ID_FIELD: record[MONGODB_ID_FIELD]},
                    replacement=record,
                    upsert=True,
                )
            )
        result = await self._get_collection().bulk_write(operations, ordered=False)
        return [str(value) for _, value in result.upserted_ids.items()]  # type: ignore

    @override
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        result = self._get_collection().find({MONGODB_ID_FIELD: {"$in": keys}})
        return await result.to_list(length=len(keys))

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
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
        """Create a new collection in MongoDB.

        This first creates a collection, with the kwargs.
        Then creates a search index based on the data model definition.

        Args:
            **kwargs: Additional keyword arguments.
        """
        collection = await self._get_database().create_collection(self.collection_name, **kwargs)
        await collection.create_search_indexes(models=_create_index_definitions(self.definition, self.index_name))

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        return bool(await self._get_database().list_collection_names(filter={"name": self.collection_name}))

    @override
    async def ensure_collection_deleted(self, **kwargs) -> None:
        await self._get_database().drop_collection(self.collection_name, **kwargs)

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if search_type == SearchType.VECTOR:
            return await self._inner_vector_search(options, values, vector, **kwargs)
        if search_type == SearchType.KEYWORD_HYBRID:
            return await self._inner_keyword_hybrid_search(options, values, vector, **kwargs)
        raise VectorStoreOperationException("Vector is required for search.")

    async def _inner_vector_search(
        self,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        vector_search_query: dict[str, Any] = {
            "limit": options.top + options.skip,
            "index": self.index_name,
            "queryVector": vector,
            "path": vector_field.storage_name or vector_field.name,
        }
        if filter := self._build_filter(options.filter):
            vector_search_query["filter"] = filter if isinstance(filter, dict) else {"$and": filter}

        projection_query: dict[str, int | dict] = {
            field: 1
            for field in self.definition.get_names(
                include_vector_fields=options.include_vectors,
                include_key_field=False,  # _id is always included
            )
        }
        projection_query[MONGODB_SCORE_FIELD] = {"$meta": "vectorSearchScore"}
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

    async def _inner_keyword_hybrid_search(
        self,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        vector_search_query: dict[str, Any] = {
            "limit": options.top + options.skip,
            "index": self.index_name,
            "queryVector": vector,
            "path": vector_field.storage_name or vector_field.name,
        }
        if filter := self._build_filter(options.filter):
            vector_search_query["filter"] = filter if isinstance(filter, dict) else {"$and": filter}

        projection_query: dict[str, int | dict] = {
            field: 1
            for field in self.definition.get_names(
                include_vector_fields=options.include_vectors,
                include_key_field=False,  # _id is always included
            )
        }
        projection_query[MONGODB_SCORE_FIELD] = {"$meta": "vectorSearchScore"}
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

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        # Comparison operations
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., 1 < x < 3) become $and of each comparison
                    values = []
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right = node.comparators[idx]
                        op = node.ops[idx]
                        values.append(self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right])))
                    return {"$and": values}
                left = self._lambda_parser(node.left)
                right = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.In():
                        return {left: {"$in": right}}
                    case ast.NotIn():
                        return {left: {"$nin": right}}
                    case ast.Eq():
                        # MongoDB allows short form: {field: value}
                        return {left: right}
                    case ast.NotEq():
                        return {left: {"$ne": right}}
                    case ast.Gt():
                        return {left: {"$gt": right}}
                    case ast.GtE():
                        return {left: {"$gte": right}}
                    case ast.Lt():
                        return {left: {"$lt": right}}
                    case ast.LtE():
                        return {left: {"$lte": right}}
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op = node.op  # type: ignore
                values = [self._lambda_parser(v) for v in node.values]
                if isinstance(op, ast.And):
                    return {"$and": values}
                if isinstance(op, ast.Or):
                    return {"$or": values}
                raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        operand = self._lambda_parser(node.operand)
                        return {"$not": operand}
                    case ast.UAdd() | ast.USub() | ast.Invert():
                        raise NotImplementedError("Unary +, -, ~ are not supported in MongoDB filters.")
            case ast.Attribute():
                # Only allow attributes that are in the data model
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return node.attr
            case ast.Name():
                # Only allow names that are in the data model
                if node.id not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.id}' not in data model (storage property names are used)."
                    )
                return node.id
            case ast.Constant():
                return node.value
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get(MONGODB_SCORE_FIELD)

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.mongo_client.close()

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        await self.mongo_client.aconnect()
        return self


@release_candidate
class MongoDBAtlasStore(VectorStore):
    """MongoDB Atlas store implementation."""

    mongo_client: AsyncMongoClient
    database_name: str

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        mongo_client: AsyncMongoClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the MongoDBAtlasStore client.

        Args:
            connection_string: The connection string for MongoDB Atlas, optional.
                Can be read from environment variables.
            database_name: The name of the database, optional. Can be read from environment variables.
            embedding_generator: The embedding generator, optional.
            mongo_client: The MongoDB client, optional.
            env_file_path: Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            kwargs: Additional keyword arguments.
        """
        managed_client = kwargs.get("managed_client", not mongo_client)
        if mongo_client:
            super().__init__(
                mongo_client=mongo_client,
                managed_client=managed_client,
                database_name=database_name or DEFAULT_DB_NAME,
                embedding_generator=embedding_generator,
            )
            return

        try:
            mongodb_atlas_settings = MongoDBAtlasSettings(
                env_file_path=env_file_path,
                connection_string=connection_string,
                database_name=database_name,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
        if not mongodb_atlas_settings.connection_string:
            raise VectorStoreInitializationException("The connection string is missing.")

        mongo_client = AsyncMongoClient(
            mongodb_atlas_settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=mongodb_atlas_settings.database_name,
            embedding_generator=embedding_generator,
        )

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> MongoDBAtlasCollection:
        return MongoDBAtlasCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            mongo_client=self.mongo_client,
            managed_client=False,
            database_name=self.database_name,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        database: AsyncDatabase = self.mongo_client.get_database(self.database_name)
        return await database.list_collection_names()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.mongo_client.close()

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        await self.mongo_client.aconnect()
        return self
