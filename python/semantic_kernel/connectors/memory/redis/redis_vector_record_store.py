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
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class RedisVectorRecordStore(VectorStoreRecordCollection[str, TModel]):
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

    @override
    async def _inner_upsert(
        self,
        records: list[Any],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[str]:
        return await asyncio.gather(*[self._single_upsert(record, collection_name) for record in records])

    async def _single_upsert(self, upsert_record: Any, collection_name: str | None = None) -> str:
        await self._database.hset(**upsert_record)
        return self._unget_redis_key(upsert_record["name"], collection_name)

    @override
    async def _inner_get(
        self, keys: list[str], collection_name: str | None = None, **kwargs
    ) -> list[dict[bytes, bytes]] | None:
        return await asyncio.gather(
            *[self._database.hgetall(self._get_redis_key(key, collection_name)) for key in keys]
        )

    @override
    async def _inner_delete(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> None:
        await self._database.delete(*[self._get_redis_key(key, collection_name) for key in keys])

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: list[dict[str, Any]],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Serialize the dict to a Redis store model."""
        results = []
        for record in records:
            result = {"mapping": {"timestamp": datetime.now().isoformat()}}
            metadata = {}
            for name, field in self._data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordVectorField):
                    if isinstance(record[name], np.ndarray):
                        result["mapping"][name] = record[name].tobytes()
                    else:
                        result["mapping"][name] = np.array(record[name]).astype(np.float64).tobytes()
                    continue
                if isinstance(field, VectorStoreRecordKeyField):
                    result["name"] = self._get_redis_key(record[name], collection_name)
                    continue
                metadata[name] = record[field.name]
            result["mapping"]["metadata"] = json.dumps(metadata)
            results.append(result)
        return results

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: list[dict[bytes, bytes]],
        keys: list[str],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        results = []
        for key, record in zip(keys, records):
            flattened = json.loads(record[b"metadata"])
            for name, field in self._data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordKeyField):
                    flattened[name] = self._unget_redis_key(key, collection_name)
                if isinstance(field, VectorStoreRecordVectorField):
                    # TODO (eavanvalkenburg): This is a temporary fix to handle the fact that
                    # the vector is returned as a bytes object, and the user needs that or a list.
                    vector = np.frombuffer(record[name.encode()], dtype=np.float64).tolist()
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

    @override
    @property
    def supported_vector_types(self) -> list[type] | None:
        """Supply the types that vectors are allowed to have. None means any."""
        return [list[float], np.ndarray]

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
