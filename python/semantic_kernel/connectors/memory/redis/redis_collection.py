# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import json
import logging
import sys
from abc import abstractmethod
from collections.abc import Sequence
from copy import copy
from typing import Any, ClassVar, Generic, TypeVar

import numpy as np
from pydantic import ValidationError
from redis.asyncio.client import Redis
from redis.commands.search.indexDefinition import IndexDefinition
from redisvl.index.index import process_results
from redisvl.query.filter import FilterExpression
from redisvl.query.query import BaseQuery, FilterQuery, VectorQuery
from redisvl.redis.utils import array_to_buffer, buffer_to_array, convert_bytes

from semantic_kernel.connectors.memory.redis.const import (
    INDEX_TYPE_MAP,
    STORAGE_TYPE_MAP,
    TYPE_MAPPER_VECTOR,
    RedisCollectionTypes,
)
from semantic_kernel.connectors.memory.redis.utils import (
    RedisWrapper,
    _filters_to_redis_filters,
    data_model_definition_to_redis_fields,
)
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorSearchResult,
    VectorTextSearchMixin,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordCollection
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorSearchOptionsException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.list_handler import desync_list

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)

TQuery = TypeVar("TQuery", bound=BaseQuery)


@experimental
class RedisCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    VectorTextSearchMixin[TKey, TModel],
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
            from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings

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
            redis_database=RedisWrapper.from_url(redis_settings.connection_string.get_secret_value()),
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
        fields = data_model_definition_to_redis_fields(self.data_model_definition, self.collection_type)
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
    async def _inner_get(self, keys: Sequence[str], **kwargs) -> Sequence[dict[str, Any]] | None:
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
            for name, field in self.data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordVectorField):
                    dtype = TYPE_MAPPER_VECTOR[field.property_type or "default"].lower()
                    if isinstance(record[name], np.ndarray):
                        result["mapping"][name] = record[name].astype(dtype).tobytes()
                    else:
                        result["mapping"][name] = array_to_buffer(record[name], dtype)
                    continue
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(record[name])
                    continue
                result["mapping"][name] = record[field.name]
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
            for field in self.data_model_definition.fields.values():
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
        for field in self.data_model_definition.fields.values():
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
    async def _inner_get(self, keys: Sequence[str], **kwargs) -> Sequence[dict[bytes, bytes]] | None:
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
            for name, field in self.data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(record[name])
                    continue
                if isinstance(field, VectorStoreRecordVectorField):
                    if isinstance(record[name], np.ndarray):
                        record[name] = record[name].tolist()
                    result["value"][name] = record[name]
                result["value"][name] = record[name]
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
        for field in self.data_model_definition.fields.values():
            match field:
                case VectorStoreRecordVectorField():
                    if include_vectors:
                        query.return_field(field.name)
                case _:
                    query.return_field(field.name)
        return query
