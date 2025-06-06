# Copyright (c) Microsoft. All rights reserved.
import logging
import sys
from collections.abc import MutableMapping, Sequence
from typing import Any, Final, Generic

import faiss
import numpy as np
from pydantic import Field

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.in_memory import IN_MEMORY_SCORE_KEY, InMemoryCollection, InMemoryStore, TKey
from semantic_kernel.data.vector import (
    DistanceFunction,
    IndexKind,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStoreCollectionDefinition,
    VectorStoreField,
)
from semantic_kernel.exceptions import VectorStoreInitializationException, VectorStoreOperationException
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreModelException

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)

DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, type[faiss.Index]]] = {
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: faiss.IndexFlatL2,
    DistanceFunction.DOT_PROD: faiss.IndexFlatIP,
    DistanceFunction.DEFAULT: faiss.IndexFlatL2,
}
INDEX_KIND_MAP: Final[dict[IndexKind, bool]] = {
    IndexKind.FLAT: True,
    IndexKind.DEFAULT: True,
}


def _create_index(field: VectorStoreField) -> faiss.Index:
    """Create a Faiss index."""
    if field.index_kind not in INDEX_KIND_MAP:
        raise VectorStoreInitializationException(f"Index kind {field.index_kind} is not supported.")
    if field.distance_function not in DISTANCE_FUNCTION_MAP:
        raise VectorStoreInitializationException(f"Distance function {field.distance_function} is not supported.")
    match field.index_kind:
        case IndexKind.FLAT | IndexKind.DEFAULT:
            match field.distance_function:
                case DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE | DistanceFunction.DEFAULT:
                    return faiss.IndexFlatL2(field.dimensions)
                case DistanceFunction.DOT_PROD:
                    return faiss.IndexFlatIP(field.dimensions)
                case _:
                    raise VectorStoreInitializationException(
                        f"Distance function {field.distance_function} is "
                        f"not supported for index kind {field.index_kind}."
                    )
        case _:
            raise VectorStoreInitializationException(f"Index with {field.index_kind} is not supported.")


class FaissCollection(InMemoryCollection[TKey, TModel], Generic[TKey, TModel]):
    """Create a Faiss collection.

    The Faiss Collection builds on the InMemoryVectorCollection,
    it maintains indexes and mappings for each vector field.
    """

    indexes: MutableMapping[str, faiss.Index] = Field(default_factory=dict)
    indexes_key_map: MutableMapping[str, MutableMapping[TKey, int]] = Field(default_factory=dict)

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
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
            record_type: The type of the data model.
            definition: The definition of the data model.
            embedding_generator: The embedding generator.
            kwargs: Additional arguments.
        """
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    def _create_indexes(self, index: faiss.Index | None = None, indexes: dict[str, faiss.Index] | None = None) -> None:
        """Create Faiss indexes for each vector field.

        Args:
            index: The index to use, this can be used when there is only one vector field.
            indexes: A dictionary of indexes, the key is the name of the vector field.
        """
        if len(self.definition.vector_fields) == 1 and index is not None:
            if not isinstance(index, faiss.Index):
                raise VectorStoreInitializationException("Index must be a subtype of faiss.Index")
            if not index.is_trained:
                raise VectorStoreInitializationException("Index must be trained before using.")
            self.indexes[self.definition.vector_fields[0].name] = index
            return
        for vector_field in self.definition.vector_fields:
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
                self.indexes[vector_field.name] = _create_index(vector_field)
            if vector_field.name not in self.indexes_key_map:
                self.indexes_key_map.setdefault(vector_field.name, {})

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
        for vector_field in self.definition.vector_fields:
            vectors_to_add = [record.get(vector_field.storage_name or vector_field.name) for record in records]
            vectors = np.array(vectors_to_add, dtype=np.float32)
            if not self.indexes[vector_field.name].is_trained:
                raise VectorStoreOperationException(
                    f"This index (of type {type(self.indexes[vector_field.name])}) requires training, "
                    "which is not supported. To train the index, "
                    f"use <collection>.indexes[{vector_field.name}].train, "
                    "see faiss docs for more details."
                )
            self.indexes[vector_field.name].add(vectors)  # type: ignore
            start = len(self.indexes_key_map[vector_field.name])
            for i, record in enumerate(records):
                key = record[self.definition.key_field.name]
                self.indexes_key_map[vector_field.name][key] = start + i
        return await super()._inner_upsert(records, **kwargs)

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        for key in keys:
            for vector_field in self.definition.vector_field_names:
                if key in self.indexes_key_map[vector_field]:
                    vector_index = self.indexes_key_map[vector_field][key]
                    self.indexes[vector_field].remove_ids(np.array([vector_index]))
                    self.indexes_key_map[vector_field].pop(key, None)
        await super()._inner_delete(keys, **kwargs)

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        for vector_field in self.definition.vector_field_names:
            if vector_field in self.indexes:
                del self.indexes[vector_field]
            if vector_field in self.indexes_key_map:
                del self.indexes_key_map[vector_field]
        await super().ensure_collection_deleted(**kwargs)

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        return bool(self.indexes)

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method."""
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        field = self.definition.try_get_vector_field(options.vector_property_name)
        if not field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        return_list = []
        # first we create the vector to search with
        np_vector = np.array(vector, dtype=np.float32).reshape(1, -1)
        # then do the actual vector search
        distances, indexes = self.indexes[field.name].search(
            np_vector, min(options.top, self.indexes[field.name].ntotal)
        )  # type: ignore[call-arg]
        # since Faiss indexes do not contain the full records,
        # we get the filtered records, this is a dict of the records that match the search filters
        # and use that to get the actual records
        filtered_records = self._get_filtered_records(options)
        # we then iterate through the results, the order is the order of relevance
        # (less or most distance, dependant on distance metric used)
        for i, index in enumerate(indexes[0]):
            key = list(self.indexes_key_map[field.name].keys())[index]
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


class FaissStore(InMemoryStore):
    """Create a Faiss store."""

    def __init__(
        self,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ):
        """Create a Faiss store."""
        super().__init__(embedding_generator=embedding_generator, **kwargs)

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> FaissCollection:
        """Get a Faiss collection."""
        return FaissCollection(
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )
