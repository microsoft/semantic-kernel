# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

import numpy as np
from pydantic import ValidationError
from redis.asyncio.client import Redis

from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.exceptions import (
    ServiceResponseException,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class RedisVectorRecordStore(VectorRecordStoreBase[str, TModel]):
    """A memory store implementation using Redis."""

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        kernel: Kernel | None = None,
        connection_string: str | None = None,
        prefix_collection_name_to_key_names: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis node connection.

        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html
        See documentation about vector attributes: https://redis.io/docs/stack/search/reference/vectors.

        """
        try:
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
            kernel=kernel,
        )
        self._database = Redis.from_url(redis_settings.connection_string.get_secret_value())
        self._prefix_collection_name_to_key_names = prefix_collection_name_to_key_names

    async def close(self):
        """Closes the Redis database connection."""
        logger.info("Closing Redis connection")
        await self._database.close()

    async def _upsert(
        self,
        record: TModel,
        collection_name: str | None = None,
        generate_embeddings: bool = True,
        **kwargs: Any,
    ) -> list[str] | None:
        if generate_embeddings:
            await self._add_vector_to_records(record)
        upsert_records = self.serialize(record, collection_name=collection_name)
        if not isinstance(upsert_records, list):
            upsert_records = [upsert_records]
        keys = []
        for upsert_record in upsert_records:
            try:
                await self._database.hset(**upsert_record)
            except Exception as e:
                raise ServiceResponseException("Could not upsert messages.") from e
            keys.append(upsert_record["name"])
        return keys if keys else None

    @override
    async def upsert(
        self,
        record: TModel,
        collection_name: str | None = None,
        generate_embeddings: bool = True,
        **kwargs: Any,
    ) -> OneOrMany[str] | None:
        result = await self._upsert(record, collection_name, generate_embeddings, **kwargs)
        if result:
            return result if self._container_mode else result[0]
        return None

    @override
    async def upsert_batch(
        self,
        records: OneOrMany[TModel],
        collection_name: str | None = None,
        generate_embeddings: bool = False,
        **kwargs,
    ) -> list[str] | None:
        return await self._upsert(records, collection_name, generate_embeddings, **kwargs)

    async def _get(self, key: str, collection_name: str | None = None) -> dict[bytes, bytes] | None:
        r_key = self._get_redis_key(key, collection_name)
        fields = await self._database.hgetall(r_key)
        if len(fields) == 0:
            return None
        return fields

    @override
    async def get(self, key: str, collection_name: str | None = None, **kwargs) -> TModel:
        fields = await self._get(key, collection_name)
        # Did not find the record
        if not fields:
            return None
        return self.deserialize(fields, keys=[key], collection_name=collection_name)

    @override
    async def get_batch(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> OneOrMany[TModel]:
        fields = await asyncio.gather(*[self._get(key, collection_name) for key in keys])
        # Did not find the record
        if not fields:
            return None
        return self.deserialize(fields, keys=keys, collection_name=collection_name)

    async def delete(self, collection_name: str, key: str) -> None:
        """Removes a memory record from the data store.

        Does not guarantee that the collection exists.
        If the key does not exist, do nothing.

        Args:
            collection_name (str): Name for a collection of embeddings
            key (str): ID associated with the memory to remove
        """
        await self._database.delete(self._get_redis_key(key, collection_name))

    async def delete_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): Name for a collection of embeddings
            keys (List[str]): IDs associated with the memory records to remove
        """
        await self._database.delete(*[self._get_redis_key(key, collection_name) for key in keys])

    def _get_redis_key(self, key: str, collection_name: str | None = None) -> str:
        if self._prefix_collection_name_to_key_names and (prefix := self._get_collection_name(collection_name)):
            return f"{prefix}:{key}"
        return key

    def _unget_redis_key(self, key: str, collection_name: str | None = None) -> str:
        if (
            self._prefix_collection_name_to_key_names
            and (prefix := self._get_collection_name(collection_name))
            and ":" in key
        ):
            return key[len(prefix) + 1 :]
        return key

    @override
    def _serialize_dict_to_store_model(
        self,
        record: list[dict[str, Any]],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Serialize the dict to a Redis store model."""
        results = []
        for rec in record:
            result = {"mapping": {"timestamp": datetime.now().isoformat()}}
            metadata = {}
            for name, field in self._data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordVectorField):
                    if isinstance(rec[name], np.ndarray):
                        result["mapping"][name] = rec[name].tobytes()
                    else:
                        result["mapping"][name] = np.array(rec[name]).astype(np.float64).tobytes()
                    continue
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(rec[name], collection_name)
                    continue
                metadata[name] = rec[field.name]
            result["mapping"]["metadata"] = json.dumps(metadata)
            results.append(result)
        return results

    @override
    def _deserialize_store_model_to_dict(
        self,
        search_result: list[dict[bytes, bytes]],
        keys: list[str],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        results = []
        for key, rec in zip(keys, search_result):
            flattened = json.loads(rec[b"metadata"])
            for name, field in self._data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordKeyField):
                    flattened[name] = self._unget_redis_key(key, collection_name)
                if isinstance(field, VectorStoreRecordVectorField):
                    vector = np.frombuffer(rec[name.encode()], dtype=np.float64).tolist()
                    if field.cast_function:
                        flattened[name] = field.cast_function(vector)
                    else:
                        flattened[name] = vector
            results.append(flattened)
        return results

    @override
    @property
    def supported_key_types(self) -> list[type] | None:
        return [str]

    @property
    def supported_vector_types(self) -> list[type] | None:
        """Supply the types that vectors are allowed to have. None means any."""
        return [list[float], np.ndarray]
