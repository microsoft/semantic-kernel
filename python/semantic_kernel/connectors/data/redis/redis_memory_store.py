# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Any, TypeVar

from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.kernel_types import OneOrMany

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

import numpy as np
import redis
from pydantic import ValidationError

from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings
from semantic_kernel.connectors.memory.redis.utils import (
    get_redis_key,
)
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.exceptions import (
    ServiceResourceNotFoundError,
    ServiceResponseException,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.kernel import Kernel
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
        vector_distance_metric: str = "COSINE",
        vector_type: str = "FLOAT32",
        vector_index_algorithm: str = "HNSW",
        query_dialect: int = 2,
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
        self._database = redis.Redis.from_url(redis_settings.connection_string.get_secret_value())
        self._ft = self._database.ft

        self._query_dialect = query_dialect
        self._vector_distance_metric = vector_distance_metric
        self._vector_index_algorithm = vector_index_algorithm
        self._vector_type_str = vector_type
        self._vector_type = np.float32 if vector_type == "FLOAT32" else np.float64
        self._prefix_collection_name_to_key_names = prefix_collection_name_to_key_names

    async def close(self):
        """Closes the Redis database connection."""
        logger.info("Closing Redis connection")
        self._database.close()

    def _get_redis_key(self, key: str, collection_name: str | None = None) -> str:
        if self._prefix_collection_name_to_key_names and (prefix := self._get_collection_name(collection_name)):
            return f"{prefix}:{key}"
        return key

    def _unget_redis_key(self, key: str, collection_name: str | None = None) -> str:
        if self._prefix_collection_name_to_key_names and (prefix := self._get_collection_name(collection_name)):
            return key[len(prefix) + 1 :]
        return key

    def _convert_model_to_list_of_dicts(
        self, records: OneOrMany[TModel], collection_name: str | None = None
    ) -> OneOrMany[dict[str, Any]]:
        """Convert the data model a list of dicts.

        Can be used as is, or overwritten by a subclass to return proper types.
        """
        dict_records = super()._convert_model_to_list_of_dicts(records)
        num_results = None if self._container_mode else len(dict_records)
        results = []
        for rec in dict_records:
            metadata = {}
            embedding = {}
            for name, field in self._data_model_definition.fields.items():
                if isinstance(field, VectorStoreRecordVectorField):
                    embedding[name] = rec[name]
                if isinstance(field, VectorStoreRecordKeyField):
                    key = self._get_redis_key(rec[name], collection_name)
                else:
                    metadata[name] = rec[field.name]
            results.append(
                {
                    "name": key,
                    "mapping": {
                        "key": key,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": metadata,
                        "embedding": embedding,
                    },
                }
            )

        return results if not num_results and num_results > 1 else results[0]

    def _convert_search_result_to_data_model(
        self, search_result: OneOrMany[dict[bytes, bytes]], collection_name: str | None = None
    ) -> OneOrMany[TModel]:
        """Convert the search result to a data model.

        Can be used as is, or overwritten by a subclass to return proper types.
        """
        results = []
        for rec in search_result:
            flattened = json.loads(rec[b"metadata"])
            flattened.extend(json.loads(rec[b"embedding"]))
            flattened["key"] = self._unget_redis_key(json.loads(flattened[b"key"]), collection_name)
            results.append(flattened)
        return super()._convert_search_result_to_data_model(results)

    @override
    async def upsert(
        self,
        record: object,
        collection_name: str | None = None,
        generate_embeddings: bool = True,
        **kwargs: Any,
    ) -> str | None:
        if generate_embeddings:
            await self._add_vector_to_records(record)
        upsert_record = self._convert_model_to_list_of_dicts(record, collection_name)
        try:
            self._database.hset(**upsert_record)
            return upsert_record["key"]
        except Exception as e:
            raise ServiceResponseException("Could not upsert messages.") from e

    @override
    async def upsert_batch(
        self,
        records: OneOrMany[TModel],
        collection_name: str | None = None,
        generate_embeddings: bool = False,
        **kwargs,
    ) -> list[str] | None:
        if generate_embeddings:
            await self._add_vector_to_records(records)
        upsert_records = self._convert_model_to_list_of_dicts(records, collection_name)
        keys = []
        for upsert_record in upsert_records:
            try:
                self._database.hset(**upsert_record)
                keys.append(upsert_record["key"])
            except Exception as e:
                raise ServiceResponseException("Could not upsert messages.") from e
        return keys

    async def _get(self, key: str, collection_name: str | None = None) -> dict[bytes, bytes] | None:
        fields = self._database.hgetall(self._get_redis_key(key, collection_name))
        if len(fields) == 0:
            return None
        return fields

    @override
    async def get(self, key: str, collection_name: str | None = None, **kwargs) -> TModel:
        fields = await self._get(key, collection_name)
        # Did not find the record
        if not fields:
            return None
        return self._convert_search_result_to_data_model(fields, collection_name)

    @override
    async def get_batch(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> OneOrMany[TModel]:
        fields = await asyncio.gather(*[self._get(key, collection_name) for key in keys])
        # Did not find the record
        if not fields:
            return None
        return self._convert_search_result_to_data_model(fields, collection_name)

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a memory record from the data store.

        Does not guarantee that the collection exists.
        If the key does not exist, do nothing.

        Args:
            collection_name (str): Name for a collection of embeddings
            key (str): ID associated with the memory to remove
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        self._database.delete(get_redis_key(collection_name, key))

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): Name for a collection of embeddings
            keys (List[str]): IDs associated with the memory records to remove
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        self._database.delete(*[get_redis_key(collection_name, key) for key in keys])
