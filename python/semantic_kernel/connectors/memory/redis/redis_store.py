# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import ValidationError
from redis.asyncio.client import Redis

from semantic_kernel.connectors.memory.redis.const import RedisCollectionTypes
from semantic_kernel.connectors.memory.redis.redis_collection import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.connectors.memory.redis.utils import RedisWrapper
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage import VectorStore, VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorStoreInitializationException
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


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
            from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings

            redis_settings = RedisSettings(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Redis settings.", ex) from ex
        super().__init__(redis_database=RedisWrapper.from_url(redis_settings.connection_string.get_secret_value()))

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
        if collection_name not in self.vector_record_collections:
            if collection_type == RedisCollectionTypes.HASHSET:
                self.vector_record_collections[collection_name] = RedisHashsetCollection(
                    data_model_type=data_model_type,
                    data_model_definition=data_model_definition,
                    collection_name=collection_name,
                    redis_database=self.redis_database,
                    **kwargs,
                )
            else:
                self.vector_record_collections[collection_name] = RedisJsonCollection(
                    data_model_type=data_model_type,
                    data_model_definition=data_model_definition,
                    collection_name=collection_name,
                    redis_database=self.redis_database,
                    **kwargs,
                )
        return self.vector_record_collections[collection_name]

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.redis_database.aclose()
