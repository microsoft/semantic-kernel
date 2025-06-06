# Copyright (c) Microsoft. All rights reserved.

import ast
import sys
from collections.abc import AsyncIterable, Callable, Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar

from numpy import dot
from pydantic import Field
from scipy.spatial.distance import cityblock, cosine, euclidean, hamming, sqeuclidean
from typing_extensions import override

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DISTANCE_FUNCTION_DIRECTION_HELPER,
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
)
from semantic_kernel.exceptions import VectorSearchExecutionException, VectorStoreModelValidationError
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreModelException, VectorStoreOperationException
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.list_handler import empty_generator

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

TKey = TypeVar("TKey", bound=str | int | float)

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


TAKey = TypeVar("TAKey", bound=str)
TAValue = TypeVar("TAValue", bound=str | int | float | list[float] | None)


class AttributeDict(dict[TAKey, TAValue], Generic[TAKey, TAValue]):
    """A dict subclass that allows attribute access to keys.

    This is used to allow the filters to work either way, using:
    - `lambda x: x.key == 'id'` or `lambda x: x['key'] == 'id'`
    """

    def __getattr__(self, name) -> TAValue:
        """Allow attribute-style access to dict keys."""
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value) -> None:
        """Allow setting dict keys via attribute access."""
        self[name] = value

    def __delattr__(self, name) -> None:
        """Allow deleting dict keys via attribute access."""
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)


class InMemoryCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """In Memory Collection."""

    inner_storage: dict[TKey, AttributeDict] = Field(default_factory=dict)
    supported_key_types: ClassVar[set[str] | None] = {"str", "int", "float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ):
        """Create a In Memory Collection."""
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    def _validate_data_model(self):
        """Check if the In Memory Score key is not used."""
        super()._validate_data_model()
        if IN_MEMORY_SCORE_KEY in self.definition.names:
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
            record = AttributeDict(record)
            self.inner_storage[record[self._key_field_name]] = record
            updated_keys.append(record[self._key_field_name])
        return updated_keys

    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return records

    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        return records

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        pass

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
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
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Inner search method."""
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        return_records: dict[TKey, float] = {}
        field = self.definition.try_get_vector_field(options.vector_property_name)
        if not field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        if field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorSearchExecutionException(
                f"Distance function '{field.distance_function}' is not supported. "
                f"Supported functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
            )
        distance_func = DISTANCE_FUNCTION_MAP[field.distance_function]  # type: ignore[assignment]

        for key, record in self._get_filtered_records(options).items():
            if vector and field is not None:
                return_records[key] = self._calculate_vector_similarity(
                    vector,
                    record[field.storage_name or field.name],
                    distance_func,
                    invert_score=field.distance_function == DistanceFunction.COSINE_SIMILARITY,
                )
        if field.distance_function == DistanceFunction.DEFAULT:
            reverse_func = DISTANCE_FUNCTION_DIRECTION_HELPER[DistanceFunction.COSINE_DISTANCE]
        else:
            reverse_func = DISTANCE_FUNCTION_DIRECTION_HELPER[field.distance_function]  # type: ignore[assignment]
        sorted_records = dict(
            sorted(
                return_records.items(),
                key=lambda item: item[1],
                reverse=reverse_func(1, 0),
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

    def _get_filtered_records(self, options: VectorSearchOptions) -> dict[TKey, AttributeDict]:
        if not options.filter:
            return self.inner_storage
        try:
            callable_filters = [
                self._parse_and_validate_filter(filter) if isinstance(filter, str) else filter
                for filter in ([options.filter] if not isinstance(options.filter, list) else options.filter)
            ]
        except Exception as e:
            raise VectorStoreOperationException(f"Error evaluating filter: {e}") from e
        filtered_records: dict[TKey, AttributeDict] = {}
        for key, record in self.inner_storage.items():
            for filter in callable_filters:
                if self._run_filter(filter, record):
                    filtered_records[key] = record
        return filtered_records

    def _parse_and_validate_filter(self, filter_str: str) -> Callable:
        """Parse and validate a string filter as a lambda expression, then return the callable."""
        forbidden_names = {"__import__", "open", "eval", "exec", "__builtins__"}
        try:
            tree = ast.parse(filter_str, mode="eval")
        except SyntaxError as e:
            raise VectorStoreOperationException(f"Filter string is not valid Python: {e}") from e
        # Only allow lambda expressions
        if not (isinstance(tree, ast.Expression) and isinstance(tree.body, ast.Lambda)):
            raise VectorStoreOperationException(
                "Filter string must be a lambda expression, e.g. 'lambda x: x.key == 1'"
            )
        # Walk the AST to look for forbidden names and attribute access
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in forbidden_names:
                raise VectorStoreOperationException(f"Use of '{node.id}' is not allowed in filter expressions.")
            if isinstance(node, ast.Attribute) and node.attr in forbidden_names:
                raise VectorStoreOperationException(f"Use of '{node.attr}' is not allowed in filter expressions.")
        try:
            code = compile(tree, filename="<filter>", mode="eval")
            func = eval(code, {"__builtins__": {}}, {})  # nosec
        except Exception as e:
            raise VectorStoreOperationException(f"Error compiling filter: {e}") from e
        if not callable(func):
            raise VectorStoreOperationException("Compiled filter is not callable.")
        return func

    def _run_filter(self, filter: Callable, record: AttributeDict[TAKey, TAValue]) -> bool:
        """Run the filter on the record, supporting attribute access."""
        try:
            return filter(record)
        except Exception as e:
            raise VectorStoreOperationException(f"Error running filter: {e}") from e

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        """Not used by InMemoryCollection, but required by the interface."""
        pass

    def _calculate_vector_similarity(
        self,
        search_vector: Sequence[float | int],
        record_vector: Sequence[float | int],
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
        """Create a In Memory Vector Store."""
        super().__init__(embedding_generator=embedding_generator, **kwargs)

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return []

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> InMemoryCollection:
        """Get a collection."""
        return InMemoryCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator or self.embedding_generator,
        )
