# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
import contextlib
import json
import logging
import sys
from abc import abstractmethod
from collections.abc import MutableSequence, Sequence
from copy import copy
from enum import Enum
from typing import Any, ClassVar, Final, Generic, TypeVar

from pydantic import SecretStr, ValidationError
from redis.asyncio.client import Redis
from redis.commands.search.field import Field as RedisField
from redis.commands.search.field import NumericField, TagField, TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redisvl.index.index import process_results
from redisvl.query.filter import FilterExpression, Num, Tag, Text
from redisvl.query.query import BaseQuery, VectorQuery
from redisvl.redis.utils import array_to_buffer, buffer_to_array, convert_bytes
from redisvl.schema import StorageType

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DistanceFunction,
    FieldTypes,
    GetFilteredRecordOptions,
    IndexKind,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    VectorStoreField,
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.list_handler import desync_list

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)

TKey = TypeVar("TKey", bound=str)
TQuery = TypeVar("TQuery", bound=BaseQuery)


class RedisCollectionTypes(str, Enum):
    """Redis collection types."""

    JSON = "json"
    HASHSET = "hashset"


STORAGE_TYPE_MAP: Final[dict[RedisCollectionTypes, StorageType]] = {
    RedisCollectionTypes.JSON: StorageType.JSON,
    RedisCollectionTypes.HASHSET: StorageType.HASH,
}
DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_SIMILARITY: "COSINE",
    DistanceFunction.DOT_PROD: "IP",
    DistanceFunction.EUCLIDEAN_DISTANCE: "L2",
    DistanceFunction.DEFAULT: "COSINE",
}
INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {
    IndexKind.HNSW: "HNSW",
    IndexKind.FLAT: "FLAT",
    IndexKind.DEFAULT: "HNSW",
}
INDEX_TYPE_MAP: Final[dict[RedisCollectionTypes, IndexType]] = {
    RedisCollectionTypes.JSON: IndexType.JSON,
    RedisCollectionTypes.HASHSET: IndexType.HASH,
}
DATATYPE_MAP_VECTOR: Final[dict[str, str]] = {
    "float": "FLOAT32",
    "int": "FLOAT16",
    "binary": "FLOAT16",
    "ndarray": "FLOAT32",
    "default": "FLOAT32",
}


def _field_to_redis_field_hashset(name: str, field: VectorStoreField) -> RedisField:
    if field.field_type == FieldTypes.VECTOR:
        if field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function {field.distance_function} is not supported. "
                f"Supported functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
            )
        if field.index_kind not in INDEX_KIND_MAP:
            raise VectorStoreOperationException(
                f"Index kind {field.index_kind} is not supported. Supported kinds are: {list(INDEX_KIND_MAP.keys())}"
            )
        return VectorField(
            name=name,
            algorithm=INDEX_KIND_MAP[field.index_kind],
            attributes={
                "type": DATATYPE_MAP_VECTOR[field.type_ or "default"],
                "dim": field.dimensions,
                "distance_metric": DISTANCE_FUNCTION_MAP[field.distance_function],
            },
        )
    if field.type_ in ["int", "float"]:
        return NumericField(name=name)
    if field.is_full_text_indexed:
        return TextField(name=name)
    return TagField(name=name)


def _field_to_redis_field_json(name: str, field: VectorStoreField) -> RedisField:
    if field.field_type == FieldTypes.VECTOR:
        if field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function {field.distance_function} is not supported. "
                f"Supported functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
            )
        if field.index_kind not in INDEX_KIND_MAP:
            raise VectorStoreOperationException(
                f"Index kind {field.index_kind} is not supported. Supported kinds are: {list(INDEX_KIND_MAP.keys())}"
            )
        return VectorField(
            name=f"$.{name}",
            algorithm=INDEX_KIND_MAP[field.index_kind],
            attributes={
                "type": DATATYPE_MAP_VECTOR[field.type_ or "default"],
                "dim": field.dimensions,
                "distance_metric": DISTANCE_FUNCTION_MAP[field.distance_function],
            },
            as_name=name,
        )
    if field.type_ in ["int", "float"]:
        return NumericField(name=f"$.{name}", as_name=name)
    if field.is_full_text_indexed:
        return TextField(name=f"$.{name}", as_name=name)
    return TagField(name=f"$.{name}", as_name=name)


def _definition_to_redis_fields(
    definition: VectorStoreCollectionDefinition, collection_type: RedisCollectionTypes
) -> list[RedisField]:
    """Create a list of fields for Redis from a definition."""
    fields: list[RedisField] = []
    for field in definition.fields:
        if field.field_type == FieldTypes.KEY:
            continue
        if collection_type == RedisCollectionTypes.HASHSET:
            fields.append(_field_to_redis_field_hashset(field.storage_name or field.name, field))  # type: ignore
        elif collection_type == RedisCollectionTypes.JSON:
            fields.append(_field_to_redis_field_json(field.storage_name or field.name, field))  # type: ignore
    return fields


@release_candidate
class RedisSettings(KernelBaseSettings):
    """Redis model settings.

    Args:
    - connection_string (str | None):
        Redis connection string (Env var REDIS_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "REDIS_"

    connection_string: SecretStr


@release_candidate
class RedisCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """A vector store record collection implementation using Redis."""

    redis_database: Redis
    prefix_collection_name_to_key_names: bool
    collection_type: RedisCollectionTypes
    supported_key_types: ClassVar[set[str] | None] = {"str"}
    supported_vector_types: ClassVar[set[str] | None] = {"float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        redis_database: Redis | None = None,
        prefix_collection_name_to_key_names: bool = True,
        collection_type: RedisCollectionTypes = RedisCollectionTypes.HASHSET,
        connection_string: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis node connection.

        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html
        See documentation about vector attributes: https://redis.io/docs/stack/search/reference/vectors.

        """
        if redis_database:
            super().__init__(
                record_type=record_type,
                definition=definition,
                collection_name=collection_name,
                embedding_generator=embedding_generator,
                redis_database=redis_database,
                prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
                collection_type=collection_type,
                managed_client=False,
                **kwargs,
            )
            return
        try:
            redis_settings = RedisSettings(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Redis settings.", ex) from ex
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator,
            redis_database=Redis.from_url(redis_settings.connection_string.get_secret_value()),
            prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
            collection_type=collection_type,
            **kwargs,
        )

    def _get_redis_key(self, key: TKey) -> TKey:
        if self.prefix_collection_name_to_key_names:
            return f"{self.collection_name}:{key}"  # type: ignore
        return key

    def _unget_redis_key(self, key: TKey) -> TKey:
        if self.prefix_collection_name_to_key_names and ":" in key:
            return key[len(self.collection_name) + 1 :]  # type: ignore
        return key

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new index in Redis.

        Args:
            **kwargs: Additional keyword arguments.
                fields (list[Fields]): The fields to create the index with, when not supplied,
                    these are created from the definition.
                index_definition (IndexDefinition): The search index to create, if this is supplied
                    this is used instead of a index created based on the definition.
                other kwargs are passed to the create_index method.
        """
        if (index_definition := kwargs.pop("index_definition", None)) and (fields := kwargs.pop("fields", None)):
            if isinstance(index_definition, IndexDefinition):
                await self.redis_database.ft(self.collection_name).create_index(
                    fields, definition=index_definition, **kwargs
                )
                return
            raise VectorStoreOperationException("Invalid index type supplied.")
        fields = _definition_to_redis_fields(self.definition, self.collection_type)
        index_definition = IndexDefinition(
            prefix=f"{self.collection_name}:", index_type=INDEX_TYPE_MAP[self.collection_type]
        )
        await self.redis_database.ft(self.collection_name).create_index(fields, definition=index_definition, **kwargs)

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        try:
            await self.redis_database.ft(self.collection_name).info()
            return True
        except Exception:
            return False

    @override
    async def ensure_collection_deleted(self, **kwargs) -> None:
        exists = await self.does_collection_exist()
        if exists:
            await self.redis_database.ft(self.collection_name).dropindex(**kwargs)
        else:
            logger.debug("Collection does not exist, skipping deletion.")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.redis_database.aclose()  # type: ignore

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        if not vector:
            raise VectorSearchExecutionException("No vector found.")
        query = self._construct_vector_query(vector, options, **kwargs)
        results = await self.redis_database.ft(self.collection_name).search(  # type: ignore
            query=query.query, query_params=query.params
        )
        processed = process_results(results, query, STORAGE_TYPE_MAP[self.collection_type])
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(desync_list(processed)),
            total_count=results.total,
        )

    def _construct_vector_query(
        self, vector: Sequence[float | int], options: VectorSearchOptions, **kwargs: Any
    ) -> VectorQuery:
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorSearchOptionsException("Vector field not found.")

        query = VectorQuery(
            vector=vector,  # type: ignore
            vector_field_name=vector_field.storage_name or vector_field.name,  # type: ignore
            num_results=options.top + options.skip,
            dialect=2,
            return_score=True,
        )
        if filter := self._build_filter(options.filter):  # type: ignore
            if isinstance(filter, list):
                expr = filter[0]
                for v in filter[1:]:
                    expr = expr & v

                query.set_filter(expr)
            else:
                query.set_filter(filter)
        query.paging(offset=options.skip, num=options.top + options.skip)
        query.sort_by(
            query.DISTANCE_ID,
            asc=(vector_field.distance_function)
            in [
                DistanceFunction.COSINE_SIMILARITY,
                DistanceFunction.DOT_PROD,
                DistanceFunction.DEFAULT,
            ],
        )
        return self._add_return_fields(query, options.include_vectors)

    @override
    def _lambda_parser(self, node: ast.AST) -> FilterExpression:
        """Parse the lambda AST and return a RedisVL FilterExpression."""

        def get_field_expr(field_name):
            # Find the field in the data model
            field = next(
                (f for f in self.definition.fields if (f.storage_name or f.name) == field_name),
                None,
            )
            if field is None:
                raise VectorStoreOperationException(f"Field '{field_name}' not found in data model.")
            if field.field_type == FieldTypes.DATA:
                if field.is_full_text_indexed:
                    return lambda: Text(field_name)
                if field.type_ in ("int", "float"):
                    return lambda: Num(field_name)
                return lambda: Tag(field_name)
            if field.field_type == FieldTypes.VECTOR:
                raise VectorStoreOperationException(f"Cannot filter on vector field '{field_name}'.")
            return lambda: Tag(field_name)

        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., 1 < x < 3) become & of each comparison
                    expr = None
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right = node.comparators[idx]
                        op = node.ops[idx]
                        sub = self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right]))
                        expr = expr & sub if expr else sub
                    return expr
                left = node.left
                right = node.comparators[0]
                op = node.ops[0]
                # Only support field op value or value op field
                if isinstance(left, (ast.Attribute, ast.Name)):
                    field_name = left.attr if isinstance(left, ast.Attribute) else left.id
                    field_expr = get_field_expr(field_name)()
                    value = self._lambda_parser(right)
                    match op:
                        case ast.Eq():
                            return field_expr == value
                        case ast.NotEq():
                            return field_expr != value
                        case ast.Gt():
                            return field_expr > value
                        case ast.GtE():
                            return field_expr >= value
                        case ast.Lt():
                            return field_expr < value
                        case ast.LtE():
                            return field_expr <= value
                        case ast.In():
                            return field_expr == value  # Tag/Text/Num support list equality
                        case ast.NotIn():
                            return ~(field_expr == value)
                    raise NotImplementedError(f"Unsupported operator: {type(op)}")
                if isinstance(right, (ast.Attribute, ast.Name)):
                    # Reverse: value op field
                    field_name = right.attr if isinstance(right, ast.Attribute) else right.id
                    field_expr = get_field_expr(field_name)()
                    value = self._lambda_parser(left)
                    match op:
                        case ast.Eq():
                            return field_expr == value
                        case ast.NotEq():
                            return field_expr != value
                        case ast.Gt():
                            return field_expr < value
                        case ast.GtE():
                            return field_expr <= value
                        case ast.Lt():
                            return field_expr > value
                        case ast.LtE():
                            return field_expr >= value
                        case ast.In():
                            return field_expr == value
                        case ast.NotIn():
                            return ~(field_expr == value)
                    raise NotImplementedError(f"Unsupported operator: {type(op)}")
                raise NotImplementedError("Comparison must be between a field and a value.")
            case ast.BoolOp():
                op = node.op  # type: ignore
                values = [self._lambda_parser(v) for v in node.values]
                if isinstance(op, ast.And):
                    expr = values[0]
                    for v in values[1:]:
                        expr = expr & v
                    return expr
                if isinstance(op, ast.Or):
                    expr = values[0]
                    for v in values[1:]:
                        expr = expr | v
                    return expr
                raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        operand = self._lambda_parser(node.operand)
                        return ~operand
                    case ast.UAdd() | ast.USub() | ast.Invert():
                        raise NotImplementedError("Unary +, -, ~ are not supported in RedisVL filters.")
            case ast.Attribute():
                # Only allow attributes that are in the data model
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return node.attr
            case ast.Name():
                # Only allow names that are in the data model
                if node.id not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.id}' not in data model (storage property names are used)."
                    )
                return node.id
            case ast.Constant():
                return node.value
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    @abstractmethod
    def _add_return_fields(self, query: TQuery, include_vectors: bool) -> TQuery:
        """Add the return fields to the query.

        There is a difference between the JSON and Hashset collections,
        this method should be overridden by the subclasses.

        """
        pass

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> Any:
        """Get a record from a result."""
        ret = result.copy()
        ret.pop("vector_distance", None)
        for key, value in ret.items():
            with contextlib.suppress(json.JSONDecodeError):
                ret[key] = json.loads(value) if isinstance(value, str) else value
        return ret

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get("vector_distance")


@release_candidate
class RedisHashsetCollection(RedisCollection[TKey, TModel], Generic[TKey, TModel]):
    """A vector store record collection implementation using Redis Hashsets."""

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        redis_database: Redis | None = None,
        prefix_collection_name_to_key_names: bool = False,
        connection_string: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis node connection.

        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html
        See documentation about vector attributes: https://redis.io/docs/stack/search/reference/vectors.

        """
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator,
            redis_database=redis_database,
            prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
            collection_type=RedisCollectionTypes.HASHSET,
            connection_string=connection_string,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            **kwargs,
        )

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[TKey]:
        return await asyncio.gather(*[self._single_upsert(record) for record in records])

    async def _single_upsert(self, upsert_record: Any) -> TKey:
        await self.redis_database.hset(**upsert_record)
        return self._unget_redis_key(upsert_record["name"])

    @override
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs,
    ) -> Sequence[dict[str, Any]] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        results = await asyncio.gather(*[self._single_get(self._get_redis_key(key)) for key in keys])
        return [result for result in results if result]

    async def _single_get(self, key: str) -> dict[str, Any] | None:
        result = await self.redis_database.hgetall(key)
        if result:
            result = convert_bytes(result)
            result[self.definition.key_name] = key
        return result

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        await self.redis_database.delete(*[self._get_redis_key(key) for key in keys])

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        """Serialize the dict to a Redis store model."""
        results: MutableSequence[dict[str, Any]] = []
        for record in records:
            result: dict[str, Any] = {"mapping": {}}
            for field in self.definition.fields:
                if field.field_type == FieldTypes.VECTOR:
                    dtype = DATATYPE_MAP_VECTOR[field.type_ or "default"].lower()
                    result["mapping"][field.storage_name or field.name] = array_to_buffer(record[field.name], dtype)
                    continue
                if field.field_type == FieldTypes.KEY:
                    result["name"] = self._get_redis_key(record[field.name])
                    continue
                result["mapping"][field.storage_name or field.name] = record[field.name]
            results.append(result)
        return results

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        results = []
        for record in records:
            rec = record.copy()
            for field in self.definition.fields:
                match field.field_type:
                    case FieldTypes.KEY:
                        rec[field.name] = self._unget_redis_key(rec[field.name])
                    case "vector":
                        dtype = DATATYPE_MAP_VECTOR[field.type_ or "default"]
                        rec[field.name] = buffer_to_array(rec[field.name], dtype)
            results.append(rec)
        return results

    def _add_return_fields(self, query: TQuery, include_vectors: bool) -> TQuery:
        """Add the return fields to the query.

        For a Hashset index this should not be decoded, that is the only difference
        between this and the JSON collection.

        """
        for field in self.definition.fields:
            match field.field_type:
                case "vector":
                    if include_vectors:
                        query.return_field(field.name, decode_field=False)
                case _:
                    query.return_field(field.name)
        return query


@release_candidate
class RedisJsonCollection(RedisCollection[TKey, TModel], Generic[TKey, TModel]):
    """A vector store record collection implementation using Redis Json."""

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        redis_database: Redis | None = None,
        prefix_collection_name_to_key_names: bool = False,
        connection_string: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis node connection.

        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html
        See documentation about vector attributes: https://redis.io/docs/stack/search/reference/vectors.

        """
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            redis_database=redis_database,
            prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
            collection_type=RedisCollectionTypes.JSON,
            connection_string=connection_string,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[TKey]:
        return await asyncio.gather(*[self._single_upsert(record) for record in records])

    async def _single_upsert(self, upsert_record: Any) -> TKey:
        await self.redis_database.json().set(upsert_record["name"], "$", upsert_record["value"])
        return self._unget_redis_key(upsert_record["name"])

    @override
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs,
    ) -> Sequence[dict[str, Any]] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        kwargs_copy = copy(kwargs)
        kwargs_copy.pop("include_vectors", None)
        redis_keys = [self._get_redis_key(key) for key in keys]
        results = await self.redis_database.json().mget(redis_keys, "$", **kwargs_copy)
        return [self._add_key(key, result[0]) for key, result in zip(redis_keys, results) if result]

    def _add_key(self, key: TKey, record: dict[str, Any]) -> dict[str, Any]:
        record[self.definition.key_name] = key
        return record

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        await asyncio.gather(*[self.redis_database.json().delete(key, **kwargs) for key in keys])

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        """Serialize the dict to a Redis store model."""
        results: MutableSequence[dict[str, Any]] = []
        for record in records:
            result: dict[str, Any] = {"value": {}}
            for field in self.definition.fields:
                if field.field_type == FieldTypes.KEY:
                    result["name"] = self._get_redis_key(record[field.name])
                    continue
                if field.field_type == "vector":
                    result["value"][field.storage_name or field.name] = record[field.name]
                result["value"][field.storage_name or field.name] = record[field.name]
            results.append(result)
        return results

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        results = []
        key_field_name = self.definition.key_name
        for record in records:
            rec = record.copy()
            rec[key_field_name] = self._unget_redis_key(record[key_field_name])
            results.append(rec)
        return results

    def _add_return_fields(self, query: TQuery, include_vectors: bool) -> TQuery:
        """Add the return fields to the query."""
        for field in self.definition.fields:
            match field.field_type:
                case FieldTypes.VECTOR:
                    if include_vectors:
                        query.return_field(field.name)
                case _:
                    query.return_field(field.name)
        return query


@release_candidate
class RedisStore(VectorStore):
    """Create a Redis Vector Store."""

    redis_database: Redis

    def __init__(
        self,
        connection_string: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        redis_database: Redis | None = None,
        **kwargs: Any,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis instance."""
        if redis_database:
            super().__init__(
                redis_database=redis_database,
                embedding_generator=embedding_generator,
                **kwargs,
            )
            return
        try:
            redis_settings = RedisSettings(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Redis settings.", ex) from ex
        super().__init__(
            redis_database=Redis.from_url(redis_settings.connection_string.get_secret_value()),
            embedding_generator=embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return [name.decode() for name in await self.redis_database.execute_command("FT._LIST")]

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        collection_type: RedisCollectionTypes = RedisCollectionTypes.HASHSET,
        **kwargs: Any,
    ) -> RedisCollection:
        """Get a RedisCollection instance.

        Args:
            record_type: The type of the data model.
            definition: The model fields, optional.
            collection_name: The name of the collection.
            embedding_generator: The embedding generator to use.
            collection_type: The type of the collection, can be JSON or HASHSET.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_type == RedisCollectionTypes.HASHSET:
            return RedisHashsetCollection(
                record_type=record_type,
                definition=definition,
                collection_name=collection_name,
                redis_database=self.redis_database,
                embedding_generator=embedding_generator or self.embedding_generator,
                **kwargs,
            )
        if collection_type == RedisCollectionTypes.JSON:
            return RedisJsonCollection(
                record_type=record_type,
                definition=definition,
                collection_name=collection_name,
                redis_database=self.redis_database,
                embedding_generator=embedding_generator or self.embedding_generator,
                **kwargs,
            )
        raise VectorStoreOperationException(
            f"Collection type {collection_type} is not supported. Supported types are: {RedisCollectionTypes}"
        )

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.redis_database.aclose()  # type: ignore
