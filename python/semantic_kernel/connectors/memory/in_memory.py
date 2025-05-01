# Copyright (c) Microsoft. All rights reserved.

import ast
import sys
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from typing import Any, ClassVar, Final, Generic

from numpy import dot
from pydantic import Field
from scipy.spatial.distance import cityblock, cosine, euclidean, hamming, sqeuclidean
from typing_extensions import override

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.const import DISTANCE_FUNCTION_DIRECTION_HELPER, DistanceFunction
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import SearchType, VectorSearch, VectorSearchOptions, VectorSearchResult
from semantic_kernel.data.vector_storage import (
    GetFilteredRecordOptions,
    TKey,
    TModel,
    VectorStore,
    VectorStoreRecordCollection,
)
from semantic_kernel.exceptions import VectorSearchExecutionException, VectorStoreModelValidationError
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreModelException
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.list_handler import empty_generator

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


IN_MEMORY_SCORE_KEY: Final[str] = "in_memory_search_score"
DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction | str, Callable[..., Any]]] = {
    DistanceFunction.COSINE_DISTANCE: cosine,
    DistanceFunction.COSINE_SIMILARITY: cosine,
    DistanceFunction.EUCLIDEAN_DISTANCE: euclidean,
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: sqeuclidean,
    DistanceFunction.MANHATTAN: cityblock,
    DistanceFunction.HAMMING: hamming,
    DistanceFunction.DOT_PROD: dot,
    DistanceFunction.DEFAULT: cosine,
}


class InMemoryCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """In Memory Collection."""

    inner_storage: dict[TKey, dict] = Field(default_factory=dict)
    supported_key_types: ClassVar[set[str] | None] = {"str", "int", "float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ):
        """Create a In Memory Collection."""
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator,
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
    async def _inner_get(
        self, keys: Sequence[TKey] | None = None, options: GetFilteredRecordOptions | None = None, **kwargs: Any
    ) -> Any | OneOrMany[TModel] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
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
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method."""
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        return_records: dict[TKey, float] = {}
        field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
        if not field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_field_name}' not found in the data model definition."
            )
        if field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorSearchExecutionException(
                f"Distance function '{field.distance_function}' is not supported. Supported functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
            )
        distance_func = DISTANCE_FUNCTION_MAP[field.distance_function]

        for key, record in self._get_filtered_records(options).items():
            if vector and field is not None:
                return_records[key] = self._calculate_vector_similarity(
                    vector,
                    record[field],
                    distance_func,
                    invert_score=field.distance_function == DistanceFunction.COSINE_SIMILARITY,
                )
        sorted_records = dict(
            sorted(
                return_records.items(),
                key=lambda item: item[1],
                reverse=DISTANCE_FUNCTION_DIRECTION_HELPER[field.distance_function](1, 0),
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

    def _get_filtered_records(self, options: VectorSearchOptions) -> dict[TKey, dict]:
        if filters := self._build_filter(options.filter):
            if not isinstance(filters, list):
                filters = [filters]
            filtered_records = {}
            for key, record in self.inner_storage.items():
                for filter in filters:
                    if filter(record):
                        filtered_records[key] = record
            return filtered_records
        return self.inner_storage

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        """Rewrite lambda AST to use dict-style access instead of attribute access."""

        class AttributeToSubscriptTransformer(ast.NodeTransformer):
            def visit_Attribute(self, node):
                # Only transform if the value is a Name (e.g., x.content)
                if isinstance(node.value, ast.Name):
                    return ast.Subscript(
                        value=node.value,
                        slice=ast.Constant(value=node.attr),
                        ctx=ast.Load(),
                    )
                return self.generic_visit(node)

        # Transform the AST
        transformer = AttributeToSubscriptTransformer()
        new_node = transformer.visit(node)
        ast.fix_missing_locations(new_node)
        return new_node

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

    def _get_record_from_result(self, result: Any) -> Any:
        return result

    def _get_score_from_result(self, result: Any) -> float | None:
        return result.get(IN_MEMORY_SCORE_KEY)


@release_candidate
class InMemoryStore(VectorStore):
    """Create a In Memory Vector Store."""

    def __init__(
        self,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ):
        super().__init__(embedding_generator=embedding_generator, **kwargs)

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return []

    @override
    def get_collection(
        self,
        data_model_type: type[TModel],
        *,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        return InMemoryCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator or self.embedding_generator,
        )
