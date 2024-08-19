# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import sys
from collections.abc import Sequence
from copy import copy
from typing import Any, ClassVar, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import numpy as np
from pydantic import ValidationError
from redis.asyncio.client import Redis
from redis.commands.search.indexDefinition import IndexDefinition

from semantic_kernel.connectors.memory.redis.const import INDEX_TYPE_MAP, RedisCollectionTypes
from semantic_kernel.connectors.memory.redis.utils import RedisWrapper, data_model_definition_to_redis_fields
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class RedisCollection(VectorStoreRecordCollection[str, TModel]):
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
            )
            return
        try:
            from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings

            redis_settings = RedisSettings.create(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise MemoryConnectorInitializationError("Failed to create Redis settings.", ex) from ex
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
            raise MemoryConnectorException("Invalid index type supplied.")
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


@experimental_class
class RedisHashsetCollection(RedisCollection):
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
    async def _inner_get(self, keys: Sequence[str], **kwargs) -> Sequence[dict[bytes, bytes]] | None:
        results = await asyncio.gather(*[self.redis_database.hgetall(self._get_redis_key(key)) for key in keys])
        return [result for result in results if result]

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
            metadata = {}
            for name, field in self.data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordVectorField):
                    if not isinstance(record[name], np.ndarray):
                        record[name] = np.array(record[name])
                    result["mapping"][name] = record[name].tobytes()
                    continue
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(record[name])
                    continue
                metadata[name] = record[field.name]
            result["mapping"]["metadata"] = json.dumps(metadata)
            results.append(result)
        return results

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: Sequence[dict[bytes, bytes]],
        keys: Sequence[str],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        results = []
        for key, record in zip(keys, records):
            if record:
                flattened = json.loads(record[b"metadata"])
                for name, field in self.data_model_definition.fields.items():
                    if isinstance(field, VectorStoreRecordKeyField):
                        flattened[name] = self._unget_redis_key(key)
                    if isinstance(field, VectorStoreRecordVectorField):
                        flattened[name] = np.frombuffer(record[name.encode()]).tolist()
                results.append(flattened)
        return results


@experimental_class
class RedisJsonCollection(RedisCollection):
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
        results = await self.redis_database.json().mget([self._get_redis_key(key) for key in keys], "$", **kwargs_copy)
        return [result[0] for result in results if result]

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
        keys: Sequence[str],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        results = []
        for key, record in zip(keys, records):
            record[self.data_model_definition.key_field_name] = self._unget_redis_key(key)
            results.append(record)
        return results
