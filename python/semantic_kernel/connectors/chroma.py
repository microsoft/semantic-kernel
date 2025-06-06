# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import MutableSequence, Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar

from chromadb import Client, Collection, GetResult, QueryResult
from chromadb.api import ClientAPI
from chromadb.api.collection_configuration import CreateCollectionConfiguration, CreateHNSWConfiguration
from chromadb.api.types import EmbeddingFunction, Space
from chromadb.config import Settings

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DistanceFunction,
    GetFilteredRecordOptions,
    IndexKind,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    _get_collection_name_from_model,
)
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreInitializationException,
    VectorStoreModelException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)

TKey = TypeVar("TKey", bound=str)


DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, Space]] = {
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: "l2",
    DistanceFunction.DOT_PROD: "ip",
    DistanceFunction.DEFAULT: "l2",
}

INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {
    IndexKind.HNSW: "hnsw",
    IndexKind.DEFAULT: "hnsw",
}


@release_candidate
class ChromaCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """Chroma vector store collection."""

    client: ClientAPI
    embedding_func: EmbeddingFunction | None = None
    supported_key_types: ClassVar[set[str] | None] = {"str"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}

    def __init__(
        self,
        record_type: type[object],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        persist_directory: str | None = None,
        client_settings: "Settings | None" = None,
        client: "ClientAPI | None" = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        embedding_func: EmbeddingFunction | None = None,
        **kwargs: Any,
    ):
        """Initialize the Chroma vector store collection.

        Args:
            record_type: The type of the data model.
            definition: The definition of the data model.
            collection_name: The name of the collection.
            persist_directory: The directory to persist the collection.
            client_settings: The settings for the Chroma client.
            client: The Chroma client.
            embedding_generator: The embedding generator to use.
                This is the Semantic Kernel embedding generator that will be used to generate the embeddings.
            embedding_func: The embedding function to use.
                This is a Chroma specific function that will be used to generate the embeddings.
            kwargs: Additional arguments to pass to the parent class.

        """
        if not collection_name:
            collection_name = _get_collection_name_from_model(record_type, definition)
        managed_client = not client
        if client is None:
            settings = client_settings or Settings()
            if persist_directory is not None:
                settings.is_persistent = True
                settings.persist_directory = persist_directory
            client = Client(settings)
        super().__init__(
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            client=client,
            managed_client=managed_client,
            embedding_func=embedding_func,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    def _get_collection(self) -> Collection:
        try:
            return self.client.get_collection(name=self.collection_name, embedding_function=self.embedding_func)
        except Exception as e:
            raise RuntimeError(f"Failed to get collection {self.collection_name}") from e

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        try:
            self.client.get_collection(name=self.collection_name, embedding_function=self.embedding_func)
            return True
        except Exception:
            return False

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create the collection.

        Will create a metadata object with the hnsw arguments.
        By default only the distance function will be set based on the data model.
        To tweak the other hnsw parameters, pass them in the kwargs.

        For example:
        ```python
        await collection.create_collection(
            configuration={"hnsw": {"max_neighbors": 16, "ef_construction": 200, "ef_search": 200}}
        )
        ```
        if the `space` is set, it will be overridden, by the distance function set in the data model.

        To use the built-in Chroma embedding functions, set the `embedding_func` parameter in the class constructor.

        Args:
            kwargs: Additional arguments are passed to the metadata parameter of the create_collection method.
                See the Chroma documentation for more details.
        """
        if self.definition.vector_fields:
            configuration = kwargs.pop("configuration", {})
            configuration = CreateCollectionConfiguration(**configuration)
            vector_field = self.definition.vector_fields[0]
            if vector_field.index_kind not in INDEX_KIND_MAP:
                raise VectorStoreInitializationException(f"Index kind {vector_field.index_kind} is not supported.")
            if vector_field.distance_function not in DISTANCE_FUNCTION_MAP:
                raise VectorStoreInitializationException(
                    f"Distance function {vector_field.distance_function} is not supported."
                )
            if "hnsw" not in configuration or configuration["hnsw"] is None:
                configuration["hnsw"] = CreateHNSWConfiguration(
                    space=DISTANCE_FUNCTION_MAP[vector_field.distance_function]
                )
            else:
                configuration["hnsw"]["space"] = DISTANCE_FUNCTION_MAP[vector_field.distance_function]
            kwargs["configuration"] = configuration
        if "get_or_create" not in kwargs:
            kwargs["get_or_create"] = True

        self.client.create_collection(name=self.collection_name, embedding_function=self.embedding_func, **kwargs)

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Delete the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except ValueError:
            logger.info(f"Collection {self.collection_name} could not be deleted because it doesn't exist.")
        except Exception as e:
            raise VectorStoreOperationException(
                f"Failed to delete collection {self.collection_name} with error: {e}"
            ) from e

    def _validate_data_model(self):
        super()._validate_data_model()
        if len(self.definition.vector_fields) > 1:
            raise VectorStoreModelValidationError(
                f"Chroma only supports one vector field, but {len(self.definition.vector_fields)} were provided."
            )

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        vector_field = self.definition.vector_fields[0]
        id_field_name = self.definition.key_name
        store_models = []
        for record in records:
            store_model = {
                "id": record[id_field_name],
                "metadata": {
                    k: v
                    for k, v in record.items()
                    if k not in [id_field_name, vector_field.storage_name or vector_field.name]
                },
            }
            if self.embedding_func:
                store_model["document"] = (record[vector_field.storage_name or vector_field.name],)
            else:
                store_model["embedding"] = record[vector_field.storage_name or vector_field.name]
            if store_model["metadata"] == {}:
                store_model.pop("metadata")
            store_models.append(store_model)
        return store_models

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        vector_field = self.definition.vector_fields[0]
        # replace back the name of the vector, content and id fields
        for record in records:
            record[self.definition.key_name] = record.pop("id")
            record[vector_field.name] = record.pop("document", None) or record.pop("embedding", None)
        return records

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        upsert_obj: dict[str, Any] = {"ids": [], "metadatas": []}
        if self.embedding_func:
            upsert_obj["documents"] = []
        else:
            upsert_obj["embeddings"] = []
        for record in records:
            upsert_obj["ids"].append(record["id"])
            if "embedding" in record:
                upsert_obj["embeddings"].append(record["embedding"])
            if "document" in record:
                upsert_obj["documents"].append(record["document"])
            if "metadata" in record:
                upsert_obj["metadatas"].append(record["metadata"])
        if not upsert_obj["metadatas"]:
            upsert_obj.pop("metadatas")
        self._get_collection().add(**upsert_obj)
        return upsert_obj["ids"]

    @override
    async def _inner_get(
        self,
        keys: Sequence[str] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> Sequence[Any] | None:
        include_vectors = kwargs.get("include_vectors", True)
        if self.embedding_func:
            include = ["documents", "metadatas"]
        elif include_vectors:
            include = ["embeddings", "metadatas"]
        else:
            include = ["metadatas"]
        args: dict[str, Any] = {"include": include}
        if keys:
            args["ids"] = keys
        if options:
            args["limit"] = options.top
            args["offset"] = options.skip
        results = self._get_collection().get(**args)
        return self._unpack_results(results, include_vectors)

    def _unpack_results(
        self, results: QueryResult | GetResult, include_vectors: bool, include_distances: bool = False
    ) -> Sequence[dict[str, Any]]:
        try:
            if isinstance(results["ids"][0], str):
                for k, v in results.items():
                    results[k] = [v]  # type: ignore
        except IndexError:
            return []
        records: MutableSequence[dict[str, Any]] = []

        # Determine available fields
        ids = results["ids"][0] if "ids" in results else []
        metadatas = results.get("metadatas")
        documents = results.get("documents")
        embeddings = results.get("embeddings")
        distances = results.get("distances")

        # Build records dynamically based on available fields
        for idx, id in enumerate(ids):
            record: dict[str, Any] = {"id": id}
            # Add vector field if present
            if documents is not None and idx < len(documents[0]):
                record["document"] = documents[0][idx]
            elif embeddings is not None and idx < len(embeddings[0]):
                record["embedding"] = embeddings[0][idx]
            # Add distance if present
            if distances is not None and isinstance(distances, list) and idx < len(distances[0]):
                record["distance"] = distances[0][idx]
            # Add metadata if present
            if metadatas is not None and idx < len(metadatas[0]) and metadatas[0] is not None:
                metadata = metadatas[0] if isinstance(metadatas[0], dict) else metadatas[0][idx]  # type: ignore
                if metadata and isinstance(metadata, dict):
                    record.update(metadata)
            records.append(record)
        return records

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        self._get_collection().delete(ids=keys)  # type: ignore

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        include = ["metadatas", "distances"]
        if options.include_vectors:
            include.append("documents" if self.embedding_func else "embeddings")
        args: dict[str, Any] = {
            "n_results": options.top,
            "include": include,
        }
        if filter := self._build_filter(options.filter):  # type: ignore
            args["where"] = filter if isinstance(filter, dict) else {"$and": filter}
        if self.embedding_func:
            args["query_texts"] = values
        elif vector is not None:
            args["query_embeddings"] = vector
        else:
            args["query_embeddings"] = await self._generate_vector_from_values(values, options)
        results = self._get_collection().query(**args)
        records = self._unpack_results(results, options.include_vectors, include_distances=True)
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(records), total_count=len(records)
        )

    @override
    def _get_record_from_result(self, result: Any) -> Any:
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        return result["distance"]

    @override
    def _lambda_parser(self, node: ast.AST) -> dict[str, Any] | str | int | float | bool | None:  # type: ignore
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
                left = self._lambda_parser(node.left)  # type: ignore
                right = self._lambda_parser(node.comparators[0])  # type: ignore
                op = node.ops[0]
                match op:
                    case ast.In():
                        return {left: {"$in": right}}  # type: ignore
                    case ast.NotIn():
                        return {left: {"$nin": right}}  # type: ignore
                    case ast.Eq():
                        # Chroma allows short form: {field: value}
                        return {left: right}  # type: ignore
                    case ast.NotEq():
                        return {left: {"$ne": right}}  # type: ignore
                    case ast.Gt():
                        return {left: {"$gt": right}}  # type: ignore
                    case ast.GtE():
                        return {left: {"$gte": right}}  # type: ignore
                    case ast.Lt():
                        return {left: {"$lt": right}}  # type: ignore
                    case ast.LtE():
                        return {left: {"$lte": right}}  # type: ignore
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
                raise NotImplementedError("Unary +, -, ~ and ! are not supported in Chroma filters.")
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


@release_candidate
class ChromaStore(VectorStore):
    """Chroma vector store."""

    client: ClientAPI

    def __init__(
        self,
        persist_directory: str | None = None,
        client_settings: "Settings | None" = None,
        client: ClientAPI | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ):
        """Initialize the Chroma vector store."""
        managed_client = not client
        settings = client_settings or Settings()
        if persist_directory is not None:
            settings.is_persistent = True
            settings.persist_directory = persist_directory
        if client is None:
            client = Client(settings)
        super().__init__(
            client=client, managed_client=managed_client, embedding_generator=embedding_generator, **kwargs
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
    ) -> ChromaCollection:
        """Get a vector record store."""
        return ChromaCollection(
            client=self.client,
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return [coll.name for coll in self.client.list_collections()]
