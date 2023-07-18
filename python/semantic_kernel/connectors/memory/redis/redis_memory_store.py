# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, List, Optional, Tuple

from numpy import ndarray

import redis
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


class RedisMemoryStore(MemoryStoreBase):
    '''
    Implementation of the MemoryStoreBase class with Redis
    '''
    _database: "redis.Redis"
    _logger: Logger

    def __init__(
        self,
        connection_string: str = None,
        database: redis.Redis = None,
        settings: Dict[str, Any] = None,
        vector_size: int = 128,
        logger: Optional[Logger] = None,
    ) -> None:
        '''
        RedisMemoryStore is an abstracted interface to interact with a Redis node connection.
        See https://redis-py.readthedocs.io/en/stable/connections.html for more details about Redis connections. 
        
        Arguments:
            connection_string {str} -- Specify the connection string of the Redis connection
            database {redis.Redis} -- Provide specific instance of a Redis connection
            settings  {Dict[str, Any]} -- Configuration settings for the Redis instance
            vector_size {int} -- Dimension of vectors within the database, default to 
            
            Note: if  "settings" and "connection_string" are both set, "settings" is prioritized
        '''

        self._database = (redis.Redis.from_url(connection_string) if connection_string 
                          else (database if database else redis.Redis()))

        if settings:
            self.configure(settings)

        assert vector_size > 0, "Vector dimension must be positive integer"
        self._vector_size = vector_size
        self._ft = self._database.ft

        self._logger = logger or NullLogger()

    def configure(self, settings: Dict[str, Any]) -> None:
        '''
        Configures the Redis database connection, consult the Redis documentation for further information: https://redis.io/commands/config-set/

        Arguments:
            settings {Dict[str, Any]} -- Desired settings in {parameter: value} format to configure the Redis connection

        Example:
            # Create a default Redis data store
            redis_ds = RedisMemoryStore()

            # Set the host and port to be localhost:6369 and authenticate with the password "redis"
            redis_ds.configure({"bind":"localhost", "port":6379, password="redis"})

        Exceptions:
            Redis exceptions if incorrect configurations are detected, see: https://redis.readthedocs.io/en/stable/exceptions.html

        Returns:
            None
        '''
        for param, val in settings.items():
            try:
                self._database.config_set(param, val)
            except Exception as e:
                print(f"Error configuring ({param}:{val})\n\t{e}")


    async def create_collection_async(self, collection_name: str) -> None:
        pass

    async def get_collection_async(
        self, collection_name: str
    ) -> List[str]:
        pass

    async def get_collections_async(self) -> List[str]:
        pass

    async def delete_collection_async(self, collection_name: str) -> None:
        pass

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        pass

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        pass

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        pass

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        pass

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        pass

    async def remove_async(self, collection_name: str, key: str) -> None:
        pass

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        pass

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = True,
    ) -> List[Tuple[MemoryRecord, float]]:
        pass

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = True,
    ) -> Tuple[MemoryRecord, float]:
        pass
