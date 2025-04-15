# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Generic

from chromadb import Client, Collection, QueryResult
from chromadb.api import ClientAPI
from chromadb.config import Settings

from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.record_definition import VectorStoreRecordDataField, VectorStoreRecordDefinition
from semantic_kernel.data.text_search import AnyTagsEqualTo, EqualTo, KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorSearchResult,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStore, VectorStoreRecordCollection
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreInitializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)


DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: "l2",
    DistanceFunction.DOT_PROD: "ip",
}


@experimental
class ChromaCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """Chroma vector store collection."""

    client: ClientAPI
    supported_key_types: ClassVar[list[str] | None] = ["str"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        persist_directory: str | None = None,
        client_settings: "Settings | None" = None,
        client: "ClientAPI | None" = None,
        **kwargs: Any,
    ):
        """Initialize the Chroma vector store collection."""
        managed_client = not client
        if client is None:
            settings = client_settings or Settings()
            if persist_directory is not None:
                settings.is_persistent = True
                settings.persist_directory = persist_directory
            client = Client(settings)
        super().__init__(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            client=client,
            managed_client=managed_client,
            **kwargs,
        )

    def _get_collection(self) -> Collection:
        try:
            return self.client.get_collection(name=self.collection_name)
        except Exception as e:
            raise RuntimeError(f"Failed to get collection {self.collection_name}") from e

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        try:
            self.client.get_collection(name=self.collection_name)
            return True
        except Exception:
            return False

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create the collection.

        Sets the distance function if specified in the data model definition.

        Args:
            kwargs: Additional arguments are passed to the metadata parameter of the create_collection method.
        """
        if self.data_model_definition.vector_fields:
            if (
                self.data_model_definition.vector_fields[0].index_kind
                and self.data_model_definition.vector_fields[0].index_kind != "hnsw"
            ):
                raise VectorStoreInitializationException(
                    f"Index kind {self.data_model_definition.vector_fields[0].index_kind} is not supported."
                )
            distance_func = (
                self.data_model_definition.vector_fields[0].distance_function
                or DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE
            )
            if distance_func not in DISTANCE_FUNCTION_MAP:
                raise VectorStoreInitializationException(
                    f"Distance function {self.data_model_definition.vector_fields[0].distance_function} is not "
                    "supported."
                )
            kwargs["hnsw:space"] = DISTANCE_FUNCTION_MAP[distance_func]
        if kwargs:
            self.client.create_collection(name=self.collection_name, metadata=kwargs)
        else:
            self.client.create_collection(name=self.collection_name)

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
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
        if len(self.data_model_definition.vector_fields) > 1:
            raise VectorStoreModelValidationError(
                "Chroma only supports one vector field, but "
                f"{len(self.data_model_definition.vector_fields)} were provided."
            )

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        vector_field_name = self.data_model_definition.vector_field_names[0]
        id_field_name = self.data_model_definition.key_field_name
        document_field_name = next(
            field.name
            for field in self.data_model_definition.fields.values()
            if isinstance(field, VectorStoreRecordDataField) and field.embedding_property_name == vector_field_name
        )
        store_models = []
        for record in records:
            store_model = {
                "id": record[id_field_name],
                "embedding": record[vector_field_name],
                "document": record[document_field_name],
                "metadata": {
                    k: v for k, v in record.items() if k not in [id_field_name, vector_field_name, document_field_name]
                },
            }
            if store_model["metadata"] == {}:
                store_model.pop("metadata")
            store_models.append(store_model)
        return store_models

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        vector_field_name = self.data_model_definition.vector_field_names[0]
        id_field_name = self.data_model_definition.key_field_name
        document_field_name = next(
            field.name
            for field in self.data_model_definition.fields.values()
            if isinstance(field, VectorStoreRecordDataField) and field.embedding_property_name == vector_field_name
        )
        # replace back the name of the vector, content and id fields
        for record in records:
            record[id_field_name] = record.pop("id")
            record[vector_field_name] = record.pop("embedding")
            record[document_field_name] = record.pop("document")
        return records

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[str]:
        upsert_obj = {"ids": []}
        for record in records:
            upsert_obj["ids"].append(record["id"])
            if "embedding" in record:
                if "embeddings" not in upsert_obj:
                    upsert_obj["embeddings"] = []
                upsert_obj["embeddings"].append(record["embedding"])
            if "document" in record:
                if "documents" not in upsert_obj:
                    upsert_obj["documents"] = []
                upsert_obj["documents"].append(record["document"])
            if "metadata" in record:
                if "metadatas" not in upsert_obj:
                    upsert_obj["metadatas"] = []
                upsert_obj["metadatas"].append(record["metadata"])
        self._get_collection().add(**upsert_obj)
        return upsert_obj["ids"]

    @override
    async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Sequence[Any]:
        include_vectors = kwargs.get("include_vectors", True)
        results = self._get_collection().get(
            ids=keys,
            include=["documents", "metadatas", "embeddings"] if include_vectors else ["documents", "metadatas"],
        )
        return self._unpack_results(results, include_vectors)

    def _unpack_results(
        self, results: QueryResult, include_vectors: bool, include_distances: bool = False
    ) -> Sequence[dict[str, Any]]:
        try:
            if isinstance(results["ids"][0], str):
                for k, v in results.items():
                    results[k] = [v]
        except IndexError:
            return []
        records = []
        if include_vectors and include_distances:
            for id, document, embedding, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["embeddings"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                record = {"id": id, "embedding": embedding, "document": document, "distance": distance}
                if metadata:
                    record.update(metadata)
                records.append(record)
            return records
        if include_vectors and not include_distances:
            for id, document, embedding, metadata in zip(
                results["ids"][0],
                results["documents"][0],
                results["embeddings"][0],
                results["metadatas"][0],
            ):
                record = {
                    "id": id,
                    "embedding": embedding,
                    "document": document,
                }
                if metadata:
                    record.update(metadata)
                records.append(record)
            return records
        if not include_vectors and include_distances:
            for id, document, metadata, distance in zip(
                results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]
            ):
                record = {"id": id, "document": document, "distance": distance}
                if metadata:
                    record.update(metadata)
                records.append(record)
            return records
        for id, document, metadata in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        ):
            record = {
                "id": id,
                "document": document,
            }
            if metadata:
                record.update(metadata)
            records.append(record)
        return records

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        self._get_collection().delete(ids=keys)

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        where = self._parse_filter(options)
        args = {
            "n_results": options.top,
            "include": ["documents", "metadatas", "embeddings", "distances"]
            if options.include_vectors
            else ["documents", "metadatas", "distances"],
        }
        if where:
            args["where"] = where
        if vector is not None:
            args["query_embeddings"] = vector
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

    def _parse_filter(self, options: VectorSearchOptions) -> dict[str, Any] | None:
        if options.filter is None or not options.filter.filters:
            return None
        filter_expression = {"$and": []}
        for filter in options.filter.filters:
            match filter:
                case EqualTo():
                    filter_expression["$and"].append({filter.field_name: {"$eq": filter.value}})
                case AnyTagsEqualTo():
                    filter_expression["$and"].append({filter.field_name: {"$in": filter.value}})
        if len(filter_expression["$and"]) == 1:
            return filter_expression["$and"][0]
        return filter_expression


@experimental
class ChromaStore(VectorStore):
    """Chroma vector store."""

    client: ClientAPI

    def __init__(
        self,
        persist_directory: str | None = None,
        client_settings: "Settings | None" = None,
        client: ClientAPI | None = None,
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
        super().__init__(client=client, managed_client=managed_client, **kwargs)

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: "VectorStoreRecordDefinition | None" = None,
        **kwargs: "Any",
    ) -> VectorStoreRecordCollection:
        """Get a vector record store."""
        return ChromaCollection(
            client=self.client,
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return self.client.list_collections()
