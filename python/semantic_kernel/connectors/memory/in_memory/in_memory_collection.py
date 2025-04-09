# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from typing import Any, ClassVar, Generic

from pydantic import Field

from semantic_kernel.connectors.memory.in_memory.const import DISTANCE_FUNCTION_MAP
from semantic_kernel.data.const import DISTANCE_FUNCTION_DIRECTION_HELPER, DistanceFunction
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import AnyTagsEqualTo, EqualTo, FilterClauseBase, KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorSearchResult,
    VectorTextSearchMixin,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorSearchExecutionException, VectorStoreModelValidationError
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.list_handler import empty_generator

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


IN_MEMORY_SCORE_KEY = "in_memory_search_score"


class InMemoryVectorCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorTextSearchMixin[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """In Memory Collection."""

    inner_storage: dict[TKey, dict] = Field(default_factory=dict)
    supported_key_types: ClassVar[list[str] | None] = ["str", "int", "float"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ):
        """Create a In Memory Collection."""
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            **kwargs,
        )

    def _validate_data_model(self):
        """Check if the In Memory Score key is not used."""
        super()._validate_data_model()
        if IN_MEMORY_SCORE_KEY in self.data_model_definition.field_names:
            raise VectorStoreModelValidationError(f"Field name '{IN_MEMORY_SCORE_KEY}' is reserved for internal use.")

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        for key in keys:
            self.inner_storage.pop(key, None)

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> Any | OneOrMany[TModel] | None:
        return [self.inner_storage[key] for key in keys if key in self.inner_storage]

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[TKey]:
        updated_keys = []
        for record in records:
            key = record[self._key_field_name] if isinstance(record, Mapping) else getattr(record, self._key_field_name)
            self.inner_storage[key] = record
            updated_keys.append(key)
        return updated_keys

    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return records

    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        return records

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        pass

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        self.inner_storage = {}

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        return True

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions | None = None,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method."""
        if search_text:
            return await self._inner_search_text(search_text, options, **kwargs)
        if vector:
            if not options:
                raise VectorSearchExecutionException("Options must be provided for vector search.")
            return await self._inner_search_vectorized(vector, options, **kwargs)
        raise VectorSearchExecutionException("Search text or vector must be provided.")

    async def _inner_search_text(
        self,
        search_text: str,
        options: VectorSearchOptions | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method."""
        return_records: dict[TKey, float] = {}
        for key, record in self._get_filtered_records(options).items():
            if self._should_add_text_search(search_text, record):
                return_records[key] = 1.0
        if return_records:
            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(
                    self._generate_return_list(return_records, options), options
                ),
                total_count=len(return_records) if options and options.include_total_count else None,
            )
        return KernelSearchResults(results=None)

    async def _inner_search_vectorized(
        self,
        vector: list[float | int],
        options: VectorSearchOptions,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        return_records: dict[TKey, float] = {}
        field = options.vector_field_name or self.data_model_definition.vector_field_names[0]
        assert isinstance(self.data_model_definition.fields.get(field), VectorStoreRecordVectorField)  # nosec
        distance_metric = (
            self.data_model_definition.fields.get(field).distance_function  # type: ignore
            or DistanceFunction.COSINE_DISTANCE
        )
        distance_func = DISTANCE_FUNCTION_MAP[distance_metric]

        for key, record in self._get_filtered_records(options).items():
            if vector and field is not None:
                return_records[key] = self._calculate_vector_similarity(
                    vector,
                    record[field],
                    distance_func,
                    invert_score=distance_metric == DistanceFunction.COSINE_SIMILARITY,
                )
        sorted_records = dict(
            sorted(
                return_records.items(),
                key=lambda item: item[1],
                reverse=DISTANCE_FUNCTION_DIRECTION_HELPER[distance_metric](1, 0),
            )
        )
        if sorted_records:
            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(
                    self._generate_return_list(sorted_records, options), options
                ),
                total_count=len(return_records) if options and options.include_total_count else None,
            )
        return KernelSearchResults(results=empty_generator())

    async def _generate_return_list(
        self, return_records: dict[TKey, float], options: VectorSearchOptions | None
    ) -> AsyncIterable[dict]:
        top = 3 if not options else options.top
        skip = 0 if not options else options.skip
        returned = 0
        for idx, key in enumerate(return_records.keys()):
            if idx >= skip:
                returned += 1
                rec = self.inner_storage[key]
                rec[IN_MEMORY_SCORE_KEY] = return_records[key]
                yield rec
                if returned >= top:
                    break

    def _get_filtered_records(self, options: VectorSearchOptions | None) -> dict[TKey, dict]:
        if options and options.filter:
            for filter in options.filter.filters:
                return {key: record for key, record in self.inner_storage.items() if self._apply_filter(record, filter)}
        return self.inner_storage

    def _should_add_text_search(self, search_text: str, record: dict) -> bool:
        for field in self.data_model_definition.fields.values():
            if not isinstance(field, VectorStoreRecordVectorField) and search_text in record.get(field.name, ""):
                return True
        return False

    def _calculate_vector_similarity(
        self,
        search_vector: list[float | int],
        record_vector: list[float | int],
        distance_func: Callable,
        invert_score: bool = False,
    ) -> float:
        calc = distance_func(record_vector, search_vector)
        if invert_score:
            return 1.0 - float(calc)
        return float(calc)

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

    def _get_record_from_result(self, result: Any) -> Any:
        return result

    def _get_score_from_result(self, result: Any) -> float | None:
        return result.get(IN_MEMORY_SCORE_KEY)
