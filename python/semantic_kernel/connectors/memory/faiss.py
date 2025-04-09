# Copyright (c) Microsoft. All rights reserved.
import logging
import sys
from collections.abc import MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, Generic

import faiss
import numpy as np
from pydantic import Field

from semantic_kernel.connectors.memory.in_memory.in_memory_collection import (
    IN_MEMORY_SCORE_KEY,
    InMemoryVectorCollection,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition, VectorStoreRecordVectorField
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import VectorSearchOptions, VectorSearchResult
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStore
from semantic_kernel.exceptions import (
    VectorStoreInitializationException,
    VectorStoreOperationException,
)

if TYPE_CHECKING:
    from semantic_kernel.data.vector_storage import VectorStoreRecordCollection


if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)


class FaissCollection(InMemoryVectorCollection[TKey, TModel], Generic[TKey, TModel]):
    """Create a Faiss collection.

    The Faiss Collection builds on the InMemoryVectorCollection,
    it maintains indexes and mappings for each vector field.
    """

    indexes: MutableMapping[str, faiss.Index] = Field(default_factory=dict)
    indexes_key_map: MutableMapping[str, MutableMapping[TKey, int]] = Field(default_factory=dict)

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
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
            kwargs: Additional arguments.
        """
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            **kwargs,
        )

    def _create_indexes(self, index: faiss.Index | None = None, indexes: dict[str, faiss.Index] | None = None) -> None:
        """Create Faiss indexes for each vector field.

        Args:
            index: The index to use, this can be used when there is only one vector field.
            indexes: A dictionary of indexes, the key is the name of the vector field.
        """
        if len(self.data_model_definition.vector_fields) == 1 and index is not None:
            if not isinstance(index, faiss.Index):
                raise VectorStoreInitializationException("Index must be a subtype of faiss.Index")
            if not index.is_trained:
                raise VectorStoreInitializationException("Index must be trained before using.")
            self.indexes[self.data_model_definition.vector_fields[0].name] = index
            return
        for vector_field in self.data_model_definition.vector_fields:
            if indexes and vector_field.name in indexes:
                if not isinstance(indexes[vector_field.name], faiss.Index):
                    raise VectorStoreInitializationException(
                        f"Index for {vector_field.name} must be a subtype of faiss.Index"
                    )
                if not indexes[vector_field.name].is_trained:
                    raise VectorStoreInitializationException(
                        f"Index for {vector_field.name} must be trained before using."
                    )
                self.indexes[vector_field.name] = indexes[vector_field.name]
                if vector_field.name not in self.indexes_key_map:
                    self.indexes_key_map.setdefault(vector_field.name, {})
                continue
            if vector_field.name not in self.indexes:
                index = self._create_index(vector_field)
                self.indexes[vector_field.name] = index
            if vector_field.name not in self.indexes_key_map:
                self.indexes_key_map.setdefault(vector_field.name, {})

    def _create_index(self, field: VectorStoreRecordVectorField) -> faiss.Index:
        """Create a Faiss index."""
        index_kind = field.index_kind or IndexKind.FLAT
        distance_function = field.distance_function or DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE
        match index_kind:
            case IndexKind.FLAT:
                match distance_function:
                    case DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE:
                        return faiss.IndexFlatL2(field.dimensions)
                    case DistanceFunction.DOT_PROD:
                        return faiss.IndexFlatIP(field.dimensions)
                    case _:
                        raise VectorStoreInitializationException(
                            f"Distance function {distance_function} is not supported for index kind {index_kind}."
                        )
            case _:
                raise VectorStoreInitializationException(f"Index with {index_kind} is not supported.")

    @override
    async def create_collection(
        self, index: faiss.Index | None = None, indexes: dict[str, faiss.Index] | None = None, **kwargs: Any
    ) -> None:
        """Create a collection.

        Considering the complexity of different faiss indexes, we support a limited set.
        For more advanced scenario's you can create your own indexes and pass them in here.
        This includes indexes that need training, or GPU-based indexes, since you would also
        need to build the faiss package for use with GPU's yourself.

        Args:
            index: The index to use, this can be used when there is only one vector field.
            indexes: A dictionary of indexes, the key is the name of the vector field.
            kwargs: Additional arguments.
        """
        self._create_indexes(index=index, indexes=indexes)

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[TKey]:
        """Upsert records."""
        for vector_field in self.data_model_definition.vector_field_names:
            vectors_to_add = [record.get(vector_field) for record in records]
            vectors = np.array(vectors_to_add, dtype=np.float32)
            if not self.indexes[vector_field].is_trained:
                raise VectorStoreOperationException(
                    f"This index (of type {type(self.indexes[vector_field])}) requires training, "
                    "which is not supported. To train the index, "
                    f"use <collection>.indexes[{vector_field}].train, "
                    "see faiss docs for more details."
                )
            self.indexes[vector_field].add(vectors)  # type: ignore[call-arg]
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
        for vector_field in self.data_model_definition.vector_field_names:
            if vector_field in self.indexes:
                del self.indexes[vector_field]
            if vector_field in self.indexes_key_map:
                del self.indexes_key_map[vector_field]
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
        if vector and field:
            return_list = []
            # since the vector index works independently of the record index,
            # we will need to get all records that adhere to the filter first
            filtered_records = self._get_filtered_records(options)
            np_vector = np.array(vector, dtype=np.float32).reshape(1, -1)
            # then do the actual vector search
            distances, indexes = self.indexes[field].search(np_vector, min(options.top, self.indexes[field].ntotal))  # type: ignore[call-arg]
            # we then iterate through the results, the order is the order of relevance
            # (less or most distance, dependant on distance metric used)
            for i, index in enumerate(indexes[0]):
                key = list(self.indexes_key_map[field].keys())[index]
                # if the key is not in the filtered records, we ignore it
                if key not in filtered_records:
                    continue
                filtered_records[key][IN_MEMORY_SCORE_KEY] = distances[0][i]
                # so we return the list in the order of the search, with the record from the inner_storage.
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
