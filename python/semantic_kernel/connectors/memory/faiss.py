# Copyright (c) Microsoft. All rights reserved.
import logging
import sys
from collections.abc import MutableMapping, Sequence
from typing import Any, ClassVar, Generic, TypeVar

import numpy as np
from pydantic import Field

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import faiss

from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.filter_clauses.any_tags_equal_to_filter_clause import AnyTagsEqualTo
from semantic_kernel.data.filter_clauses.equal_to_filter_clause import EqualTo
from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import VectorStoreRecordVectorField
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
from semantic_kernel.data.vector_storage.vector_store import VectorStore
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreInitializationException
from semantic_kernel.kernel_types import OneOrMany

logger = logging.getLogger(__name__)

DISTANCE_FUNCTION_MAP: dict[DistanceFunction, Any] = {
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: faiss.METRIC_L2,
    DistanceFunction.DOT_PROD: faiss.METRIC_INNER_PRODUCT,
    DistanceFunction.MANHATTAN: faiss.METRIC_L1,
}


KEY_TYPES = str | int | float

TModel = TypeVar("TModel")

VECTOR_FIELD_INDEX_FIELD_NAME = "{field_name}_idx"
FAISS_SCORE_KEY = "faiss_search_score"


class FaissCollection(VectorSearchBase[KEY_TYPES, TModel], VectorizedSearchMixin[TModel], Generic[TModel]):
    """Create a Faiss collection."""

    enabled_gpu: bool = False
    inner_storage: dict[KEY_TYPES, dict] = Field(default_factory=dict)
    indexes: MutableMapping[str, faiss.Index] = Field(default_factory=dict)
    indexes_key_map: MutableMapping[str, MutableMapping[KEY_TYPES, int]] = Field(default_factory=dict)
    gpu_indexes: MutableMapping[str, faiss.Index] = Field(default_factory=dict)
    gpu_indexes_key_map: MutableMapping[str, MutableMapping[KEY_TYPES, int]] = Field(default_factory=dict)
    supported_key_types: ClassVar[list[str] | None] = ["str", "int", "float"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        enable_gpu: bool = False,
        **kwargs: Any,
    ):
        """Create a Faiss Collection."""
        if enable_gpu:
            try:
                assert faiss.StandardGpuResources  # nosec
            except AttributeError:
                logger.warning("Faiss GPU is not enabled on this system, ignoring enable_gpu.")
                enable_gpu = False
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            enabled_gpu=enable_gpu,
            **kwargs,
        )

    def _validate_data_model(self):
        """Check if the In Memory Score key is not used."""
        super()._validate_data_model()
        if len(self.data_model_definition.vector_fields) == 0:
            raise VectorStoreInitializationException(
                "A Faiss Collection must have at least one vector, otherwise use InMemoryCollections."
            )
        for vector_field in self.data_model_definition.vector_field_names:
            if VECTOR_FIELD_INDEX_FIELD_NAME.format(field_name=vector_field) in self.data_model_definition.fields:
                raise VectorStoreInitializationException(
                    f"Field {VECTOR_FIELD_INDEX_FIELD_NAME.format(field_name=vector_field)} is reserved for Faiss."
                )

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create a collection."""
        for vector_field in self.data_model_definition.vector_fields:
            metric = DISTANCE_FUNCTION_MAP.get(vector_field.distance_function, faiss.METRIC_L2)
            print(metric)
            if vector_field.index_kind == IndexKind.FLAT:
                self.indexes[vector_field.name] = faiss.IndexFlat(vector_field.dimensions)
                if self.enabled_gpu:
                    self.gpu_indexes[vector_field.name] = faiss.index_cpu_to_gpu(
                        faiss.StandardGpuResources(), 0, self.indexes[vector_field.name]
                    )
            if vector_field.index_kind == IndexKind.IVF_FLAT:
                self.indexes[vector_field.name] = faiss.IndexIVFFlat(
                    faiss.IndexFlatL2(vector_field.dimensions), vector_field.dimensions, 10
                )
                if self.enabled_gpu:
                    self.gpu_indexes[vector_field.name] = faiss.index_cpu_to_gpu(
                        faiss.StandardGpuResources(), 0, self.indexes[vector_field.name]
                    )
            self.indexes_key_map.setdefault(vector_field.name, {})
            self.gpu_indexes_key_map.setdefault(vector_field.name, {})

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[KEY_TYPES]:
        """Upsert records."""
        for vector_field in self.data_model_definition.vector_field_names:
            vectors = np.array([record.pop(vector_field) for record in records], dtype=np.float32)
            self.indexes[vector_field].add(vectors)
            if self.enabled_gpu:
                self.gpu_indexes[vector_field].add(vectors)
            start = len(self.indexes_key_map[vector_field])
            gpu_start = len(self.gpu_indexes_key_map[vector_field])
            for i, record in enumerate(records):
                key = record[self.data_model_definition.key_field.name]
                self.indexes_key_map[vector_field][key] = start + i
                if self.enabled_gpu:
                    self.gpu_indexes_key_map[vector_field][key] = gpu_start + i
        updated_keys = []
        for record in records:
            key = record[self.data_model_definition.key_field.name]
            self.inner_storage[key] = record
            updated_keys.append(key)

        return updated_keys

    @override
    async def _inner_get(self, keys: Sequence[KEY_TYPES], **kwargs: Any) -> Any | OneOrMany[TModel] | None:
        """Get records."""
        partial = {key: self.inner_storage[key] for key in keys if key in self.inner_storage}
        if kwargs.get("include_vectors"):
            for vector_field in self.data_model_definition.vector_field_names:
                for key in keys:
                    if key in self.indexes_key_map[vector_field]:
                        vector_index = self.indexes_key_map[vector_field][key]
                        partial[key][vector_field] = self.indexes[vector_field].reconstruct(vector_index).tolist()
        if partial:
            return list(partial.values())
        return None

    @override
    async def _inner_delete(self, keys: Sequence[KEY_TYPES], **kwargs: Any) -> None:
        for key in keys:
            for vector_field in self.data_model_definition.vector_field_names:
                if key in self.indexes_key_map[vector_field]:
                    vector_index = self.indexes_key_map[vector_field][key]
                    self.indexes[vector_field].remove_ids(np.array([vector_index]))
                    if self.enabled_gpu:
                        self.gpu_indexes[vector_field].remove_ids(np.array([vector_index]))
                    self.indexes_key_map[vector_field].pop(key, None)
                    self.gpu_indexes_key_map[vector_field].pop(key, None)
            self.inner_storage.pop(key, None)

    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return records

    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        return records

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        self.inner_storage = {}
        self.indexes = {}
        self.gpu_indexes = {}

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        return bool(self.indexes)

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions | None = None,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if not options.vector_field_name:
            raise ValueError("Vector field name must be provided in options for vector search.")
        field = options.vector_field_name
        assert isinstance(self.data_model_definition.fields.get(field), VectorStoreRecordVectorField)  # nosec
        if vector:
            return_list = []
            filtered_records = self._get_filtered_records(options)
            vector = np.array(vector, dtype=np.float32).reshape(1, -1)
            if self.enabled_gpu:
                distances, indexes = self.gpu_indexes[field].search(vector, options.top_k)
            else:
                distances, indexes = self.indexes[field].search(vector, options.top)
            for i, index in enumerate(indexes[0]):
                key = list(self.indexes_key_map[field].keys())[index]
                if key not in filtered_records:
                    continue
                filtered_records[key][field] = self.indexes[field].reconstruct(int(index)).tolist()
                filtered_records[key][FAISS_SCORE_KEY] = distances[0][i]
                return_list.append(filtered_records[key])

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(return_list, options),
            total_count=len(return_list) if options and options.include_total_count else None,
        )

    def _get_record_from_result(self, result: Any) -> Any:
        return result

    def _get_score_from_result(self, result: Any) -> float | None:
        return result.get(FAISS_SCORE_KEY)

    def _get_filtered_records(self, options: VectorSearchOptions | None) -> dict[KEY_TYPES, dict]:
        if options and options.filter:
            for filter in options.filter.filters:
                return {key: record for key, record in self.inner_storage.items() if self._apply_filter(record, filter)}
        return self.inner_storage

    @staticmethod
    def _apply_filter(record: dict[str, Any], filter: FilterClauseBase) -> bool:
        match filter:
            case EqualTo():
                value = record.get(filter.field_name)
                if not value:
                    return False
                return value.lower() == filter.value.lower()
            case AnyTagsEqualTo():
                tag_list = record.get(filter.field_name)
                if not tag_list:
                    return False
                if not isinstance(tag_list, list):
                    tag_list = [tag_list]
                return filter.value in tag_list
            case _:
                return True


class FaissStore(VectorStore):
    """Create a Faiss store."""

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return self.vector_record_collections.keys()

    @override
    async def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition=None,
        **kwargs,
    ) -> FaissCollection:
        self.vector_record_collections[collection_name] = FaissCollection(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            **kwargs,
        )
        return self.vector_record_collections[collection_name]
