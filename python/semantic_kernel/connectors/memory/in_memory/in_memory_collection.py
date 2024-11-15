# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from typing import Any, ClassVar, TypeVar

from pydantic import Field

from semantic_kernel.data.filter_clauses.any_tags_equal_to_filter_clause import AnyTagsEqualTo
from semantic_kernel.data.filter_clauses.equal_to_filter_clause import EqualTo

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.memory.in_memory.const import DISTANCE_FUNCTION_MAP
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.filter_clauses.filter_clause_base import FilterClauseBase
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vector_text_search import VectorTextSearchMixin
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
from semantic_kernel.exceptions import VectorSearchExecutionException, VectorStoreModelValidationError
from semantic_kernel.kernel_types import OneOrMany

KEY_TYPES = str | int | float

TModel = TypeVar("TModel")

IN_MEMORY_SCORE_KEY = "in_memory_search_score"


class InMemoryVectorCollection(
    VectorSearchBase[KEY_TYPES, TModel], VectorTextSearchMixin[TModel], VectorizedSearchMixin[TModel]
):
    """In Memory Collection."""

    inner_storage: dict[KEY_TYPES, dict] = Field(default_factory=dict)
    supported_key_types: ClassVar[list[str] | None] = ["str", "int", "float"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
    ):
        """Create a In Memory Collection."""
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
        )

    def _validate_data_model(self):
        """Check if the In Memory Score key is not used."""
        super()._validate_data_model()
        if IN_MEMORY_SCORE_KEY in self.data_model_definition.field_names:
            raise VectorStoreModelValidationError(f"Field name '{IN_MEMORY_SCORE_KEY}' is reserved for internal use.")

    @override
    async def _inner_delete(self, keys: Sequence[KEY_TYPES], **kwargs: Any) -> None:
        for key in keys:
            self.inner_storage.pop(key, None)

    @override
    async def _inner_get(self, keys: Sequence[KEY_TYPES], **kwargs: Any) -> Any | OneOrMany[TModel] | None:
        return [self.inner_storage[key] for key in keys if key in self.inner_storage]

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[KEY_TYPES]:
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
        return_records: dict[KEY_TYPES, float] = {}
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
        return_records: dict[KEY_TYPES, float] = {}
        if not options.vector_field_name:
            raise ValueError("Vector field name must be provided in options for vector search.")
        field = options.vector_field_name
        assert isinstance(self.data_model_definition.fields.get(field), VectorStoreRecordVectorField)  # nosec
        distance_metric = self.data_model_definition.fields.get(field).distance_function or "default"  # type: ignore
        distance_func = DISTANCE_FUNCTION_MAP[distance_metric]

        for key, record in self._get_filtered_records(options).items():
            if vector and field is not None:
                return_records[key] = self._calculate_vector_similarity(
                    vector,
                    record[field],
                    distance_func,
                    invert_score=distance_metric == DistanceFunction.COSINE_SIMILARITY,
                )
        if distance_metric in [DistanceFunction.COSINE_SIMILARITY, DistanceFunction.DOT_PROD]:
            sorted_records = dict(sorted(return_records.items(), key=lambda item: item[1], reverse=True))
        else:
            sorted_records = dict(sorted(return_records.items(), key=lambda item: item[1]))
        if sorted_records:
            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(
                    self._generate_return_list(sorted_records, options), options
                ),
                total_count=len(return_records) if options and options.include_total_count else None,
            )
        return KernelSearchResults(results=None)

    async def _generate_return_list(
        self, return_records: dict[KEY_TYPES, float], options: VectorSearchOptions | None
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

    def _get_filtered_records(self, options: VectorSearchOptions | None) -> dict[KEY_TYPES, dict]:
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
