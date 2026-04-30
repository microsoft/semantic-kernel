# Copyright (c) Microsoft. All rights reserved.

import ast
import sys
from collections.abc import AsyncIterable, Callable, Mapping, Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar, cast

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


class ReadOnlyAttributeDict(Mapping[TAKey, TAValue], Generic[TAKey, TAValue]):
    """A read-only mapping that allows attribute access to keys."""

    def __init__(self, data: Mapping[TAKey, TAValue]):
        """Initialize the read-only mapping wrapper."""
        self._data = data

    def __getitem__(self, key: TAKey) -> TAValue:
        """Get a value by key."""
        return self._wrap_value(self._data[key])

    def __iter__(self):
        """Iterate over keys."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of keys."""
        return len(self._data)

    def __getattr__(self, name: str) -> TAValue:
        """Allow attribute-style access to mapping keys."""
        try:
            return self._wrap_value(self._data[cast(TAKey, name)])
        except KeyError:
            raise AttributeError(name)

    @staticmethod
    def _wrap_value(value: Any) -> Any:
        """Wrap nested mappings to preserve read-only attribute access."""
        if isinstance(value, Mapping) and not isinstance(value, ReadOnlyAttributeDict):
            return ReadOnlyAttributeDict(value)
        return value


class _SafeFilterEvaluator:
    """Evaluate a restricted filter AST without using eval()."""

    def __init__(
        self,
        *,
        direct_call_functions: dict[str, Callable[..., Any]],
        blocked_attributes: set[str],
        max_literal_collection_size: int,
        max_sequence_repeat_size: int,
    ):
        self._direct_call_functions = direct_call_functions
        self._blocked_attributes = blocked_attributes
        self._max_literal_collection_size = max_literal_collection_size
        self._max_sequence_repeat_size = max_sequence_repeat_size

    def evaluate(self, node: ast.AST, context: Mapping[str, Any]) -> Any:
        """Evaluate a supported AST node."""
        evaluator = getattr(self, f"_eval_{type(node).__name__}", None)
        if evaluator is None:
            raise VectorStoreOperationException(
                f"AST node type '{type(node).__name__}' is not supported during filter evaluation."
            )
        return evaluator(node, context)

    def _eval_Constant(self, node: ast.Constant, context: Mapping[str, Any]) -> Any:
        """Evaluate a constant literal."""
        del context
        if isinstance(node.value, str) and len(node.value) > self._max_literal_collection_size:
            raise VectorStoreOperationException(
                "String literals in filter expressions exceed the maximum allowed size."
            )
        return node.value

    def _eval_Name(self, node: ast.Name, context: Mapping[str, Any]) -> Any:
        """Evaluate a variable reference."""
        if node.id not in context:
            raise VectorStoreOperationException(f"Use of name '{node.id}' is not allowed in filter expressions.")
        return context[node.id]

    def _eval_Attribute(self, node: ast.Attribute, context: Mapping[str, Any]) -> Any:
        """Evaluate an attribute access."""
        if node.attr in self._blocked_attributes:
            raise VectorStoreOperationException(
                f"Access to attribute '{node.attr}' is not allowed in filter expressions."
            )
        value = self.evaluate(node.value, context)
        try:
            return ReadOnlyAttributeDict._wrap_value(getattr(value, node.attr))
        except AttributeError as e:
            raise VectorStoreOperationException(
                f"Attribute '{node.attr}' is not available in filter expressions."
            ) from e

    def _eval_Subscript(self, node: ast.Subscript, context: Mapping[str, Any]) -> Any:
        """Evaluate an index or slice operation."""
        value = self.evaluate(node.value, context)
        slice_value = self.evaluate(node.slice, context)
        try:
            return ReadOnlyAttributeDict._wrap_value(value[slice_value])
        except Exception as e:
            raise VectorStoreOperationException(f"Error evaluating subscript access: {e}") from e

    def _eval_Slice(self, node: ast.Slice, context: Mapping[str, Any]) -> slice:
        """Evaluate a slice node."""
        lower = self._evaluate_optional(node.lower, context)
        upper = self._evaluate_optional(node.upper, context)
        step = self._evaluate_optional(node.step, context)
        return slice(lower, upper, step)

    def _eval_List(self, node: ast.List, context: Mapping[str, Any]) -> list[Any]:
        """Evaluate a list literal."""
        self._ensure_literal_collection_size(len(node.elts))
        return [self.evaluate(element, context) for element in node.elts]

    def _eval_Tuple(self, node: ast.Tuple, context: Mapping[str, Any]) -> tuple[Any, ...]:
        """Evaluate a tuple literal."""
        self._ensure_literal_collection_size(len(node.elts))
        return tuple(self.evaluate(element, context) for element in node.elts)

    def _eval_Set(self, node: ast.Set, context: Mapping[str, Any]) -> set[Any]:
        """Evaluate a set literal."""
        self._ensure_literal_collection_size(len(node.elts))
        return {self.evaluate(element, context) for element in node.elts}

    def _eval_Dict(self, node: ast.Dict, context: Mapping[str, Any]) -> dict[Any, Any]:
        """Evaluate a dict literal."""
        self._ensure_literal_collection_size(len(node.keys))
        result: dict[Any, Any] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                raise VectorStoreOperationException("Dictionary unpacking is not allowed in filter expressions.")
            result[self.evaluate(key, context)] = self.evaluate(value, context)
        return result

    def _eval_BoolOp(self, node: ast.BoolOp, context: Mapping[str, Any]) -> Any:
        """Evaluate boolean operators with Python short-circuit semantics."""
        if isinstance(node.op, ast.And):
            result = self.evaluate(node.values[0], context)
            for value in node.values[1:]:
                if not result:
                    return result
                result = self.evaluate(value, context)
            return result
        if isinstance(node.op, ast.Or):
            result = self.evaluate(node.values[0], context)
            for value in node.values[1:]:
                if result:
                    return result
                result = self.evaluate(value, context)
            return result
        raise VectorStoreOperationException(
            f"Boolean operator '{type(node.op).__name__}' is not allowed in filter expressions."
        )

    def _eval_UnaryOp(self, node: ast.UnaryOp, context: Mapping[str, Any]) -> Any:
        """Evaluate a unary operator."""
        operand = self.evaluate(node.operand, context)
        if isinstance(node.op, ast.Not):
            return not operand
        raise VectorStoreOperationException(
            f"Unary operator '{type(node.op).__name__}' is not allowed in filter expressions."
        )

    def _eval_Compare(self, node: ast.Compare, context: Mapping[str, Any]) -> bool:
        """Evaluate a comparison expression."""
        left = self.evaluate(node.left, context)
        for operator_node, comparator in zip(node.ops, node.comparators, strict=True):
            right = self.evaluate(comparator, context)
            if not self._compare(operator_node, left, right):
                return False
            left = right
        return True

    def _eval_BinOp(self, node: ast.BinOp, context: Mapping[str, Any]) -> Any:
        """Evaluate a binary operator."""
        left = self.evaluate(node.left, context)
        right = self.evaluate(node.right, context)

        if isinstance(node.op, ast.Add):
            return self._safe_add(left, right)
        if isinstance(node.op, ast.Sub):
            return self._safe_numeric_operation(node.op, left, right, lambda a, b: a - b)
        if isinstance(node.op, ast.Mult):
            return self._safe_mult(left, right)
        if isinstance(node.op, ast.Div):
            return self._safe_numeric_operation(node.op, left, right, lambda a, b: a / b)
        if isinstance(node.op, ast.Mod):
            return self._safe_numeric_operation(node.op, left, right, lambda a, b: a % b)
        if isinstance(node.op, ast.FloorDiv):
            return self._safe_numeric_operation(node.op, left, right, lambda a, b: a // b)

        raise VectorStoreOperationException(
            f"Binary operator '{type(node.op).__name__}' is not allowed in filter expressions."
        )

    def _eval_Call(self, node: ast.Call, context: Mapping[str, Any]) -> Any:
        """Evaluate a function or method call."""
        args = [self.evaluate(arg, context) for arg in node.args]

        if isinstance(node.func, ast.Name):
            try:
                func = self._direct_call_functions[node.func.id]
            except KeyError as e:
                raise VectorStoreOperationException(
                    f"Function '{node.func.id}' is only supported as a method call in filter expressions."
                ) from e
            return func(*args)

        if isinstance(node.func, ast.Attribute):
            target = self.evaluate(node.func.value, context)
            if node.func.attr == "contains":
                if len(args) != 1:
                    raise VectorStoreOperationException("Method 'contains' expects exactly one argument.")
                return args[0] in target

            try:
                func = getattr(target, node.func.attr)
            except AttributeError as e:
                raise VectorStoreOperationException(
                    f"Method '{node.func.attr}' is not available in filter expressions."
                ) from e

            if not callable(func):
                raise VectorStoreOperationException(
                    f"Attribute '{node.func.attr}' is not callable in filter expressions."
                )
            return func(*args)

        raise VectorStoreOperationException(
            f"Call target node type '{type(node.func).__name__}' is not allowed in filter expressions."
        )

    def _compare(self, operator_node: ast.AST, left: Any, right: Any) -> bool:
        """Evaluate a comparison operator."""
        if isinstance(operator_node, ast.Eq):
            return left == right
        if isinstance(operator_node, ast.NotEq):
            return left != right
        if isinstance(operator_node, ast.Lt):
            return left < right
        if isinstance(operator_node, ast.LtE):
            return left <= right
        if isinstance(operator_node, ast.Gt):
            return left > right
        if isinstance(operator_node, ast.GtE):
            return left >= right
        if isinstance(operator_node, ast.In):
            return left in right
        if isinstance(operator_node, ast.NotIn):
            return left not in right
        if isinstance(operator_node, ast.Is):
            return left is right
        if isinstance(operator_node, ast.IsNot):
            return left is not right
        raise VectorStoreOperationException(
            f"Comparison operator '{type(operator_node).__name__}' is not allowed in filter expressions."
        )

    def _safe_add(self, left: Any, right: Any) -> Any:
        """Safely evaluate addition."""
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left + right
        if isinstance(left, str) and isinstance(right, str):
            return self._ensure_sequence_result_size(left, right, lambda a, b: a + b)
        if isinstance(left, list) and isinstance(right, list):
            return self._ensure_sequence_result_size(left, right, lambda a, b: a + b)
        if isinstance(left, tuple) and isinstance(right, tuple):
            return self._ensure_sequence_result_size(left, right, lambda a, b: a + b)
        raise VectorStoreOperationException(
            "Addition in filter expressions is only allowed for numeric values and same-type sequences."
        )

    def _safe_mult(self, left: Any, right: Any) -> Any:
        """Safely evaluate multiplication."""
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left * right
        if isinstance(left, int) and isinstance(right, (str, list, tuple)):
            return self._safe_repeat(right, left)
        if isinstance(right, int) and isinstance(left, (str, list, tuple)):
            return self._safe_repeat(left, right)
        raise VectorStoreOperationException(
            "Multiplication in filter expressions is only allowed for numeric values and bounded sequence repetition."
        )

    def _safe_repeat(self, value: str | list[Any] | tuple[Any, ...], repeat_count: int) -> Any:
        """Safely repeat a sequence."""
        if repeat_count <= 0 or len(value) == 0:
            return value * repeat_count
        if len(value) > self._max_sequence_repeat_size // repeat_count:
            raise VectorStoreOperationException(
                "Sequence repetition in filter expressions exceeds the maximum allowed size."
            )
        return value * repeat_count

    def _safe_numeric_operation(
        self,
        operator_node: ast.AST,
        left: Any,
        right: Any,
        operation: Callable[[float | int, float | int], Any],
    ) -> Any:
        """Safely evaluate a numeric binary operation."""
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise VectorStoreOperationException(
                f"Operator '{type(operator_node).__name__}' is only allowed for numeric values in filter expressions."
            )
        return operation(left, right)

    def _ensure_literal_collection_size(self, size: int) -> None:
        """Reject excessively large literal collections."""
        if size > self._max_literal_collection_size:
            raise VectorStoreOperationException(
                "Collection literals in filter expressions exceed the maximum allowed size."
            )

    def _ensure_sequence_result_size(
        self,
        left: str | list[Any] | tuple[Any, ...],
        right: str | list[Any] | tuple[Any, ...],
        operation: Callable[[Any, Any], Any],
    ) -> Any:
        """Reject oversized sequence concatenation results."""
        if len(left) + len(right) > self._max_sequence_repeat_size:
            raise VectorStoreOperationException(
                "Sequence operations in filter expressions exceed the maximum allowed size."
            )
        return operation(left, right)

    def _evaluate_optional(self, node: ast.AST | None, context: Mapping[str, Any]) -> Any:
        """Evaluate an optional AST node."""
        return self.evaluate(node, context) if node is not None else None


class InMemoryCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """In Memory Collection."""

    inner_storage: dict[TKey, AttributeDict] = Field(default_factory=dict)
    supported_key_types: ClassVar[set[str] | None] = {"str", "int", "float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}
    # Conservative defaults: callers can raise these per collection instance or subclass if needed.
    max_filter_source_length: int = Field(default=2_048, exclude=True)
    max_filter_ast_node_count: int = Field(default=128, exclude=True)
    max_filter_literal_collection_size: int = Field(default=256, exclude=True)
    max_filter_sequence_repeat_size: int = Field(default=1_024, exclude=True)

    # Allowlist of AST node types permitted in filter expressions.
    # This can be overridden in subclasses to extend or restrict allowed operations.
    allowed_filter_ast_nodes: ClassVar[set[type]] = {
        ast.Expression,
        ast.Lambda,
        ast.arguments,
        ast.arg,
        # Comparisons and boolean operations
        ast.Compare,
        ast.BoolOp,
        ast.UnaryOp,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.In,
        ast.NotIn,
        ast.Is,
        ast.IsNot,
        # Data access
        ast.Name,
        ast.Load,
        ast.Attribute,
        ast.Subscript,
        ast.Slice,
        # Literals
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.Set,
        ast.Dict,
        # Basic arithmetic (useful for computed comparisons)
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.FloorDiv,
        # Function calls (restricted to safe builtins separately)
        ast.Call,
    }

    # Allowlist of function/method names that can be called in filter expressions.
    allowed_filter_functions: ClassVar[set[str]] = {
        "len",
        "str",
        "int",
        "float",
        "bool",
        "abs",
        "min",
        "max",
        "sum",
        "any",
        "all",
        "lower",
        "upper",
        "strip",
        "startswith",
        "endswith",
        "contains",
        "get",
        "keys",
        "values",
        "items",
    }
    direct_filter_functions: ClassVar[dict[str, Callable[..., Any]]] = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "any": any,
        "all": all,
    }

    # Blocklist of dangerous attribute names that cannot be accessed in filter expressions.
    # These attributes can be used to escape the sandbox and execute arbitrary code.
    blocked_filter_attributes: ClassVar[set[str]] = {
        # Object introspection - can lead to class/module access
        "__class__",
        "__base__",
        "__bases__",
        "__mro__",
        "__subclasses__",
        # Code and function internals
        "__code__",
        "__globals__",
        "__closure__",
        "__func__",
        "__self__",
        "__dict__",
        "__slots__",
        # Attribute access hooks
        "__getattr__",
        "__getattribute__",
        "__setattr__",
        "__delattr__",
        "__setitem__",
        "__delitem__",
        # Import and builtins
        "__builtins__",
        "__import__",
        "__loader__",
        "__spec__",
        # Module attributes
        "__name__",
        "__qualname__",
        "__module__",
        "__file__",
        "__path__",
        "__package__",
        # Descriptor protocol
        "__get__",
        "__set__",
        "__delete__",
        # Metaclass and creation
        "__new__",
        "__init__",
        "__init_subclass__",
        "__prepare__",
        "__call__",
        # Other dangerous attributes
        "__reduce__",
        "__reduce_ex__",
        "__getstate__",
        "__setstate__",
        "func_globals",  # Python 2 compatibility name
        "gi_frame",  # Generator frame access
        "gi_code",
        "f_globals",  # Frame globals
        "f_locals",
        "f_builtins",
        "co_consts",  # Code object constants
    }

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ):
        """Create a In Memory Collection.

        In Memory collections are ephemeral and exist only in memory.
        They do not persist data to disk or any external storage.

        > [Important]
        > Filters are powerful things, so make sure to not allow untrusted input here.
        > Filters for this collection are parsed into Python's `ast` module and evaluated by a restricted interpreter.
        > We only allow certain AST nodes and functions to be used in filter expressions, and we reject expressions
        > that exceed reasonable size and complexity limits.
        >
        > The default filter limits are:
        > - `max_filter_source_length=2048`
        > - `max_filter_ast_node_count=128`
        > - `max_filter_literal_collection_size=256`
        > - `max_filter_sequence_repeat_size=1024`
        > You can override these limits by passing them through `kwargs` or by setting them on the collection
        > instance after initialization.

        """
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
    async def ensure_collection_exists(self, **kwargs: Any) -> None:
        pass

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        self.inner_storage = {}

    @override
    async def collection_exists(self, **kwargs: Any) -> bool:
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
        """Parse and validate a string filter as a lambda expression, then return the callable.

        Uses an allowlist approach - only explicitly permitted AST node types and function names
        are allowed. This can be customized by overriding `allowed_filter_ast_nodes` and
        `allowed_filter_functions` class attributes.
        """
        if len(filter_str) > self.max_filter_source_length:
            raise VectorStoreOperationException("Filter string exceeds the maximum allowed length.")

        try:
            tree = ast.parse(filter_str, mode="eval")
        except SyntaxError as e:
            raise VectorStoreOperationException(f"Filter string is not valid Python: {e}") from e

        # Only allow lambda expressions at the top level
        if not (isinstance(tree, ast.Expression) and isinstance(tree.body, ast.Lambda)):
            raise VectorStoreOperationException(
                "Filter string must be a lambda expression, e.g. 'lambda x: x.key == 1'"
            )

        # Get the lambda parameter name(s) to allow them as valid Name nodes
        lambda_node = tree.body
        lambda_param_names = {arg.arg for arg in lambda_node.args.args}
        lambda_param_order = [arg.arg for arg in lambda_node.args.args]
        # Walk the AST to validate all nodes against the allowlist
        for node_count, node in enumerate(ast.walk(tree), start=1):
            if node_count > self.max_filter_ast_node_count:
                raise VectorStoreOperationException("Filter expression exceeds the maximum allowed complexity.")

            node_type = type(node)

            # Check if the node type is allowed
            if node_type not in self.allowed_filter_ast_nodes:
                raise VectorStoreOperationException(
                    f"AST node type '{node_type.__name__}' is not allowed in filter expressions."
                )

            # For Attribute nodes, validate that dangerous dunder attributes are not accessed
            if isinstance(node, ast.Attribute) and node.attr in self.blocked_filter_attributes:
                raise VectorStoreOperationException(
                    f"Access to attribute '{node.attr}' is not allowed in filter expressions. "
                    "This attribute could be used to escape the filter sandbox."
                )

            # For Name nodes, only allow the lambda parameter
            if isinstance(node, ast.Name) and node.id not in lambda_param_names:
                raise VectorStoreOperationException(
                    f"Use of name '{node.id}' is not allowed in filter expressions. "
                    f"Only the lambda parameter(s) ({', '.join(lambda_param_names)}) can be used."
                )

            # For Call nodes, validate that only allowed functions are called
            if isinstance(node, ast.Call):
                func_name: str
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                else:
                    raise VectorStoreOperationException(
                        f"Call target node type '{type(node.func).__name__}' is not allowed in filter expressions. "
                        "Only direct function and method calls are supported."
                    )

                if func_name not in self.allowed_filter_functions:
                    raise VectorStoreOperationException(
                        f"Function '{func_name}' is not allowed in filter expressions. "
                        f"Allowed functions: {', '.join(sorted(self.allowed_filter_functions))}"
                    )

            if (
                isinstance(node, (ast.List, ast.Tuple, ast.Set))
                and len(node.elts) > self.max_filter_literal_collection_size
            ):
                raise VectorStoreOperationException(
                    "Collection literals in filter expressions exceed the maximum allowed size."
                )

            if isinstance(node, ast.Dict) and len(node.keys) > self.max_filter_literal_collection_size:
                raise VectorStoreOperationException(
                    "Collection literals in filter expressions exceed the maximum allowed size."
                )

            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and len(node.value) > self.max_filter_literal_collection_size
            ):
                raise VectorStoreOperationException(
                    "String literals in filter expressions exceed the maximum allowed size."
                )

        evaluator = _SafeFilterEvaluator(
            direct_call_functions=self.direct_filter_functions,
            blocked_attributes=self.blocked_filter_attributes,
            max_literal_collection_size=self.max_filter_literal_collection_size,
            max_sequence_repeat_size=self.max_filter_sequence_repeat_size,
        )

        def filter_callable(*args: Any) -> Any:
            if len(args) != len(lambda_param_order):
                raise VectorStoreOperationException(
                    f"Filter expected {len(lambda_param_order)} argument(s), but received {len(args)}."
                )
            context = {
                name: ReadOnlyAttributeDict._wrap_value(value)
                for name, value in zip(lambda_param_order, args, strict=True)
            }
            return evaluator.evaluate(lambda_node.body, context)

        return filter_callable

    def _run_filter(self, filter: Callable, record: AttributeDict[TAKey, TAValue]) -> bool:
        """Run the filter on the record, supporting attribute access."""
        try:
            return filter(ReadOnlyAttributeDict(record))
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
