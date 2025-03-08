# Copyright (c) Microsoft. All rights reserved.
import logging
import sys
from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, Generic

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import faiss
import numpy as np
from pydantic import Field

from semantic_kernel.connectors.memory.in_memory.in_memory_collection import (
    IN_MEMORY_SCORE_KEY,
    InMemoryVectorCollection,
    TKey,
    TModel,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import VectorStoreRecordVectorField
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_storage.vector_store import VectorStore
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreInitializationException

if TYPE_CHECKING:
    from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection

logger = logging.getLogger(__name__)

DEFAULT_IVF_NLIST = 100
DEFAULT_HNSW_M = 32


class FaissCollection(InMemoryVectorCollection[TKey, TModel], Generic[TKey, TModel]):
    """Create a Faiss collection.

    The Faiss Collection builds on the InMemoryVectorCollection.
    It adds Faiss Indexes for each of the vector fields.
    """

    enabled_gpu: bool = False
    indexes: MutableMapping[str, faiss.Index] = Field(default_factory=dict)
    indexes_key_map: MutableMapping[str, MutableMapping[TKey, int]] = Field(default_factory=dict)

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        enable_gpu: bool = False,
        **kwargs: Any,
    ):
        """Create a Faiss Collection.

        To allow more complex index setups, you can pass them in here:
        ```python
        import faiss

        index = faiss.IndexFlatL2(128)
        FaissCollection(..., indexes={"vector_field_name": index})
        ```

        or you can manually add them to the indexes field of the collection.

        Args:
            collection_name: The name of the collection.
            data_model_type: The type of the data model.
            data_model_definition: The definition of the data model.
            enable_gpu: Enable GPU indexes and searches.
            kwargs: Additional arguments.
        """
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

    def _create_index(self, field: VectorStoreRecordVectorField, **kwargs: Any) -> faiss.Index:
        """Create a Faiss index."""
        new_index: faiss.Index | None = None
        index_kind = field.index_kind or IndexKind.FLAT
        distance_function = field.distance_function or DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE
        match index_kind:
            case IndexKind.FLAT:
                match distance_function:
                    case DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE:
                        new_index = faiss.IndexFlatL2(field.dimensions)
                    case DistanceFunction.DOT_PROD:
                        new_index = faiss.IndexFlatIP(field.dimensions)
                    case DistanceFunction.MANHATTAN:
                        new_index = faiss.IndexFlat(field.dimensions, faiss.METRIC_L1)
            case IndexKind.IVF_FLAT:
                n_list = kwargs.get("n_list", DEFAULT_IVF_NLIST)
                match distance_function:
                    case DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE:
                        new_index = faiss.IndexIVFFlat(
                            faiss.IndexFlatL2(field.dimensions), field.dimensions, n_list, faiss.METRIC_L2
                        )
                    case DistanceFunction.DOT_PROD:
                        new_index = faiss.IndexIVFFlat(
                            faiss.IndexFlatIP(field.dimensions), field.dimensions, n_list, faiss.METRIC_INNER_PRODUCT
                        )
                    case DistanceFunction.MANHATTAN:
                        new_index = faiss.IndexIVFFlat(
                            faiss.IndexFlat(field.dimensions, faiss.METRIC_L1),
                            field.dimensions,
                            n_list,
                            faiss.METRIC_L1,
                        )
            case IndexKind.HNSW:
                hnsw_m = kwargs.get("hnsw_m", DEFAULT_HNSW_M)
                match distance_function:
                    case DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE:
                        new_index = faiss.IndexHNSWFlat(field.dimensions, hnsw_m, faiss.METRIC_L2)
                    case DistanceFunction.DOT_PROD:
                        new_index = faiss.IndexHNSWFlat(field.dimensions, hnsw_m, faiss.METRIC_INNER_PRODUCT)
                    case DistanceFunction.MANHATTAN:
                        new_index = faiss.IndexHNSWFlat(field.dimensions, hnsw_m, faiss.METRIC_L1)
        if not new_index:
            raise VectorStoreInitializationException(
                f"Index with {field.index_kind} and {field.distance_function} is not supported."
            )
        if self.enabled_gpu:
            return faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, new_index)
        return new_index

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create a collection.

        Create a Faiss index for each vector field.

        Args:
            kwargs: Additional arguments, used for different setups:
                n_list: The number of lists for the IVF index.
                hnsw_m: The number of neighbors for the HNSW index.
        """
        for vector_field in self.data_model_definition.vector_fields:
            if vector_field.name not in self.indexes:
                index = self._create_index(vector_field, **kwargs)
                self.indexes[vector_field.name] = index
            if vector_field.name not in self.indexes_key_map:
                self.indexes_key_map.setdefault(vector_field.name, {})

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[TKey]:
        """Upsert records."""
        for vector_field in self.data_model_definition.vector_field_names:
            vectors_to_add = [record.get(vector_field) for record in records]
            vectors = np.array(vectors_to_add, dtype=np.float32)
            if not self.indexes[vector_field].is_trained:
                logger.info(f"This index for {vector_field} is not trained, training now.")
                self.indexes[vector_field].train(vectors)
            self.indexes[vector_field].add(vectors)
            start = len(self.indexes_key_map[vector_field])
            for i, record in enumerate(records):
                key = record[self.data_model_definition.key_field.name]
                self.indexes_key_map[vector_field][key] = start + i
        return await super()._inner_upsert(records, **kwargs)

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        for key in keys:
            for vector_field in self.data_model_definition.vector_field_names:
                if key in self.indexes_key_map[vector_field]:
                    vector_index = self.indexes_key_map[vector_field][key]
                    self.indexes[vector_field].remove_ids(np.array([vector_index]))
                    self.indexes_key_map[vector_field].pop(key, None)
        await super()._inner_delete(keys, **kwargs)

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        self.indexes = {}
        self.indexes_key_map = {}
        await super().delete_collection(**kwargs)

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        return bool(self.indexes)

    async def _inner_search_vectorized(
        self,
        vector: list[float | int],
        options: VectorSearchOptions,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        field = options.vector_field_name or self.data_model_definition.vector_field_names[0]
        assert isinstance(self.data_model_definition.fields.get(field), VectorStoreRecordVectorField)  # nosec
        if vector:
            return_list = []
            filtered_records = self._get_filtered_records(options)
            np_vector = np.array(vector, dtype=np.float32).reshape(1, -1)
            distances, indexes = self.indexes[field].search(np_vector, min(options.top, self.indexes[field].ntotal))
            for i, index in enumerate(indexes[0]):
                key = list(self.indexes_key_map[field].keys())[index]
                if key not in filtered_records:
                    continue
                filtered_records[key][IN_MEMORY_SCORE_KEY] = distances[0][i]
                return_list.append(filtered_records[key])

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(return_list, options),
            total_count=len(return_list) if options and options.include_total_count else None,
        )


class FaissStore(VectorStore):
    """Create a Faiss store."""

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return list(self.vector_record_collections.keys())

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition=None,
        **kwargs,
    ) -> "VectorStoreRecordCollection":
        self.vector_record_collections[collection_name] = FaissCollection(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            **kwargs,
        )
        return self.vector_record_collections[collection_name]
