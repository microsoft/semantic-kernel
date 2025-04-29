# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import json
import logging
import sys
from abc import abstractmethod
from collections.abc import Callable, Sequence
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
from redisvl.query.query import BaseQuery, FilterQuery, VectorQuery
from redisvl.redis.utils import array_to_buffer, buffer_to_array, convert_bytes
from redisvl.schema import StorageType

from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import VectorSearch, VectorSearchOptions, VectorSearchResult
from semantic_kernel.data.vector_storage import (
    GetFilteredRecordOptions,
    TKey,
    TModel,
    VectorStore,
    VectorStoreRecordCollection,
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OptionalOneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.list_handler import desync_list

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)


TQuery = TypeVar("TQuery", bound=BaseQuery)


class RedisCollectionTypes(str, Enum):
    """Redis collection types."""

    JSON = "json"
    HASHSET = "hashset"


INDEX_TYPE_MAP: Final[dict[RedisCollectionTypes, IndexType]] = {
    RedisCollectionTypes.JSON: IndexType.JSON,
    RedisCollectionTypes.HASHSET: IndexType.HASH,
}
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
TYPE_MAPPER_VECTOR: Final[dict[str, str]] = {
    "float": "FLOAT32",
    "int": "FLOAT16",
    "binary": "FLOAT16",
    "ndarray": "FLOAT32",
    "default": "FLOAT32",
}


def _field_to_redis_field_hashset(
    name: str, field: VectorStoreRecordVectorField | VectorStoreRecordDataField
) -> RedisField:
    if isinstance(field, VectorStoreRecordVectorField):
        if field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function {field.distance_function} is not supported. "
                f"Supported functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
            )
        return VectorField(
            name=name,
            algorithm=field.index_kind.value.upper() if field.index_kind else "HNSW",
            attributes={
                "type": TYPE_MAPPER_VECTOR[field.property_type or "default"],
                "dim": field.dimensions,
                "distance_metric": DISTANCE_FUNCTION_MAP[field.distance_function],
            },
        )
    if field.property_type in ["int", "float"]:
        return NumericField(name=name)
    if field.is_full_text_indexed:
        return TextField(name=name)
    return TagField(name=name)


def _field_to_redis_field_json(
    name: str, field: VectorStoreRecordVectorField | VectorStoreRecordDataField
) -> RedisField:
    if isinstance(field, VectorStoreRecordVectorField):
        if field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function {field.distance_function} is not supported. "
                f"Supported functions are: {list(DISTANCE_FUNCTION_MAP.keys())}"
            )
        return VectorField(
            name=f"$.{name}",
            algorithm=field.index_kind.value.upper() if field.index_kind else "HNSW",
            attributes={
                "type": TYPE_MAPPER_VECTOR[field.property_type or "default"],
                "dim": field.dimensions,
                "distance_metric": DISTANCE_FUNCTION_MAP[field.distance_function],
            },
            as_name=name,
        )
    if field.property_type in ["int", "float"]:
        return NumericField(name=f"$.{name}", as_name=name)
    if field.is_full_text_indexed:
        return TextField(name=f"$.{name}", as_name=name)
    return TagField(name=f"$.{name}", as_name=name)


def _data_model_definition_to_redis_fields(
    data_model_definition: VectorStoreRecordDefinition, collection_type: RedisCollectionTypes
) -> list[RedisField]:
    """Create a list of fields for Redis from a data_model_definition."""
    fields: list[RedisField] = []
    for field in data_model_definition.fields:
        if isinstance(field, VectorStoreRecordKeyField):
            continue
        if collection_type == RedisCollectionTypes.HASHSET:
            fields.append(_field_to_redis_field_hashset(field.storage_property_name or field.name, field))
        elif collection_type == RedisCollectionTypes.JSON:
            fields.append(_field_to_redis_field_json(field.storage_property_name or field.name, field))
    return fields


def _filters_to_redis_filters(
    filters: VectorSearchFilter | Callable,
    data_model_definition: VectorStoreRecordDefinition,
) -> FilterExpression | None:
    """Convert filters to Redis filters."""
    if not isinstance(filters, VectorSearchFilter):
        raise VectorStoreOperationException("Lambda filters are not supported yet.")
    if not filters.filters:
        return None
    expression: FilterExpression | None = None
    for filter in filters.filters:
        new: FilterExpression | None = None
        field = data_model_definition.fields.get(filter.field_name)
        text_field = (field.is_full_text_indexed if isinstance(field, VectorStoreRecordDataField) else False) or False
        match filter:
            case EqualTo():
                match filter.value:
                    case int() | float():
                        new = (
                            Num(filter.field_name) == filter.value  # type: ignore
                            if text_field
                            else Tag(filter.field_name) == filter.value
                        )
                    case str():
                        new = (
                            Text(filter.field_name) == filter.value
                            if text_field
                            else Tag(filter.field_name) == filter.value
                        )
                    case _:
                        raise VectorSearchOptionsException(f"Unsupported filter value type: {type(filter.value)}")
            case AnyTagsEqualTo():
                new = Text(filter.field_name) == filter.value
            case _:
                raise VectorSearchOptionsException(f"Unsupported filter type: {type(filter)}")
        if new:
            expression = expression & new if expression else new
    return expression


@experimental
class RedisSettings(KernelBaseSettings):
    """Redis model settings.

    Args:
    - connection_string (str | None):
        Redis connection string (Env var REDIS_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "REDIS_"

    connection_string: SecretStr


@experimental
class RedisCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """A vector store record collection implementation using Redis."""

    redis_database: Redis
    prefix_collection_name_to_key_names: bool
    collection_type: RedisCollectionTypes
    supported_key_types: ClassVar[list[str] | None] = ["str"]
    supported_vector_types: ClassVar[list[str] | None] = ["float"]

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
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
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                redis_database=redis_database,
                prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
                collection_type=collection_type,
                managed_client=False,
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
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            redis_database=Redis.from_url(redis_settings.connection_string.get_secret_value()),
            prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
            collection_type=collection_type,
        )

    def _get_redis_key(self, key: str) -> str:
        if self.prefix_collection_name_to_key_names:
            return f"{self.collection_name}:{key}"
        return key

    def _unget_redis_key(self, key: str) -> str:
        if self.prefix_collection_name_to_key_names and ":" in key:
            return key[len(self.collection_name) + 1 :]
        return key

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new index in Redis.

        Args:
            **kwargs: Additional keyword arguments.
                fields (list[Fields]): The fields to create the index with, when not supplied,
                    these are created from the data_model_definition.
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
        fields = _data_model_definition_to_redis_fields(self.data_model_definition, self.collection_type)
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
    async def delete_collection(self, **kwargs) -> None:
        exists = await self.does_collection_exist()
        if exists:
            await self.redis_database.ft(self.collection_name).dropindex(**kwargs)
        else:
            logger.debug("Collection does not exist, skipping deletion.")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.redis_database.aclose()

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        keywords: OptionalOneOrMany[str] = None,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if vector is not None:
            query = self._construct_vector_query(vector, options, **kwargs)
        elif search_text:
            query = self._construct_text_query(search_text, options, **kwargs)
        elif vectorizable_text:
            raise VectorSearchExecutionException("Vectorizable text search not supported.")
        results = await self.redis_database.ft(self.collection_name).search(
            query=query.query, query_params=query.params
        )
        processed = process_results(results, query, STORAGE_TYPE_MAP[self.collection_type])
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(desync_list(processed)),
            total_count=results.total,
        )

    def _construct_vector_query(
        self, vector: list[float | int], options: VectorSearchOptions, **kwargs: Any
    ) -> VectorQuery:
        vector_field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
        if not vector_field:
            raise VectorSearchOptionsException("Vector field not found.")
        query = VectorQuery(
            vector=vector,
            vector_field_name=vector_field.name,  # type: ignore
            filter_expression=_filters_to_redis_filters(options.filter, self.data_model_definition),
            num_results=options.top + options.skip,
            dialect=2,
            return_score=True,
        )
        query.paging(offset=options.skip, num=options.top + options.skip)
        query.sort_by(
            query.DISTANCE_ID,
            asc=(vector_field.distance_function or "default")
            in [
                DistanceFunction.COSINE_SIMILARITY,
                DistanceFunction.DOT_PROD,
            ],
        )
        return self._add_return_fields(query, options.include_vectors)

    def _construct_text_query(self, search_text: str, options: VectorSearchOptions, **kwargs: Any) -> FilterQuery:
        query = FilterQuery(
            FilterExpression(_filter=search_text)
            & _filters_to_redis_filters(options.filter, self.data_model_definition),
            num_results=options.top + options.skip,
            dialect=2,
        )
        query.paging(offset=options.skip, num=options.top + options.skip)
        return self._add_return_fields(query, options.include_vectors)

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


@experimental
class RedisHashsetCollection(RedisCollection[TKey, TModel], Generic[TKey, TModel]):
    """A vector store record collection implementation using Redis Hashsets."""

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
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
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            redis_database=redis_database,
            prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
            collection_type=RedisCollectionTypes.HASHSET,
            connection_string=connection_string,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            **kwargs,
        )

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[str]:
        return await asyncio.gather(*[self._single_upsert(record) for record in records])

    async def _single_upsert(self, upsert_record: Any) -> str:
        await self.redis_database.hset(**upsert_record)
        return self._unget_redis_key(upsert_record["name"])

    @override
    async def _inner_get(
        self,
        keys: Sequence[str] | None = None,
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
            result[self.data_model_definition.key_field_name] = key
        return result

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        await self.redis_database.delete(*[self._get_redis_key(key) for key in keys])

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        """Serialize the dict to a Redis store model."""
        results = []
        for record in records:
            result = {"mapping": {}}
            for field in self.data_model_definition.fields:
                if isinstance(field, VectorStoreRecordVectorField):
                    dtype = TYPE_MAPPER_VECTOR[field.property_type or "default"].lower()
                    result["mapping"][field.storage_property_name or field.name] = array_to_buffer(
                        record[field.name], dtype
                    )
                    continue
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(record[field.name])
                    continue
                result["mapping"][field.storage_property_name or field.name] = record[field.name]
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
            for field in self.data_model_definition.fields:
                match field:
                    case VectorStoreRecordKeyField():
                        rec[field.name] = self._unget_redis_key(rec[field.name])
                    case VectorStoreRecordVectorField():
                        dtype = TYPE_MAPPER_VECTOR[field.property_type or "default"]
                        rec[field.name] = buffer_to_array(rec[field.name], dtype)
            results.append(rec)
        return results

    def _add_return_fields(self, query: TQuery, include_vectors: bool) -> TQuery:
        """Add the return fields to the query.

        For a Hashset index this should not be decoded, that is the only difference
        between this and the JSON collection.

        """
        for field in self.data_model_definition.fields:
            match field:
                case VectorStoreRecordVectorField():
                    if include_vectors:
                        query.return_field(field.name, decode_field=False)
                case _:
                    query.return_field(field.name)
        return query


@experimental
class RedisJsonCollection(RedisCollection[TKey, TModel], Generic[TKey, TModel]):
    """A vector store record collection implementation using Redis Json."""

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
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
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            redis_database=redis_database,
            prefix_collection_name_to_key_names=prefix_collection_name_to_key_names,
            collection_type=RedisCollectionTypes.JSON,
            connection_string=connection_string,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            **kwargs,
        )

    @override
    async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[str]:
        return await asyncio.gather(*[self._single_upsert(record) for record in records])

    async def _single_upsert(self, upsert_record: Any) -> str:
        await self.redis_database.json().set(upsert_record["name"], "$", upsert_record["value"])
        return self._unget_redis_key(upsert_record["name"])

    @override
    async def _inner_get(
        self,
        keys: Sequence[str] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs,
    ) -> Sequence[dict[bytes, bytes]] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        kwargs_copy = copy(kwargs)
        kwargs_copy.pop("include_vectors", None)
        redis_keys = [self._get_redis_key(key) for key in keys]
        results = await self.redis_database.json().mget(redis_keys, "$", **kwargs_copy)
        return [self._add_key(key, result[0]) for key, result in zip(redis_keys, results) if result]

    def _add_key(self, key: str, record: dict[str, Any]) -> dict[str, Any]:
        record[self.data_model_definition.key_field_name] = key
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
        results = []
        for record in records:
            result = {"value": {}}
            for field in self.data_model_definition.fields:
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(record[field.name])
                    continue
                if isinstance(field, VectorStoreRecordVectorField):
                    result["value"][field.storage_property_name or field.name] = record[field.name]
                result["value"][field.storage_property_name or field.name] = record[field.name]
            results.append(result)
        return results

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        results = []
        key_field_name = self.data_model_definition.key_field_name
        for record in records:
            rec = record.copy()
            rec[key_field_name] = self._unget_redis_key(record[key_field_name])
            results.append(rec)
        return results

    def _add_return_fields(self, query: TQuery, include_vectors: bool) -> TQuery:
        """Add the return fields to the query."""
        for field in self.data_model_definition.fields:
            match field:
                case VectorStoreRecordVectorField():
                    if include_vectors:
                        query.return_field(field.name)
                case _:
                    query.return_field(field.name)
        return query


@experimental
class RedisStore(VectorStore):
    """Create a Redis Vector Store."""

    redis_database: Redis

    def __init__(
        self,
        connection_string: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        redis_database: Redis | None = None,
        **kwargs: Any,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis node connection.

        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html
        See documentation about vector attributes: https://redis.io/docs/stack/search/reference/vectors.

        """
        if redis_database:
            super().__init__(redis_database=redis_database, managed_client=False)
            return
        try:
            from semantic_kernel.connectors.memory.redis import RedisSettings

            redis_settings = RedisSettings(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Redis settings.", ex) from ex
        super().__init__(redis_database=Redis.from_url(redis_settings.connection_string.get_secret_value()))

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return [name.decode() for name in await self.redis_database.execute_command("FT._LIST")]

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_type: RedisCollectionTypes = RedisCollectionTypes.HASHSET,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a RedisCollection..

        Args:
            collection_name (str): The name of the collection.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            collection_type (RedisCollectionTypes): The type of the collection, can be JSON or HASHSET.

            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_type == RedisCollectionTypes.HASHSET:
            return RedisHashsetCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                redis_database=self.redis_database,
                **kwargs,
            )
        return RedisJsonCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            redis_database=self.redis_database,
            **kwargs,
        )

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.redis_database.aclose()
