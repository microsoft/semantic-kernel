# Copyright (c) Microsoft. All rights reserved.


from enum import Enum

from redis.commands.search.indexDefinition import IndexType
from redisvl.schema import StorageType

from semantic_kernel.data.const import DistanceFunction


class RedisCollectionTypes(str, Enum):
    JSON = "json"
    HASHSET = "hashset"


INDEX_TYPE_MAP = {
    RedisCollectionTypes.JSON: IndexType.JSON,
    RedisCollectionTypes.HASHSET: IndexType.HASH,
}

STORAGE_TYPE_MAP = {
    RedisCollectionTypes.JSON: StorageType.JSON,
    RedisCollectionTypes.HASHSET: StorageType.HASH,
}

DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_SIMILARITY: "COSINE",
    DistanceFunction.DOT_PROD: "IP",
    DistanceFunction.EUCLIDEAN_DISTANCE: "L2",
    "default": "COSINE",
}

TYPE_MAPPER_VECTOR = {
    "float": "FLOAT32",
    "int": "FLOAT16",
    "binary": "FLOAT16",
    "ndarray": "FLOAT32",
    "default": "FLOAT32",
}

__all__ = [
    "DISTANCE_FUNCTION_MAP",
    "TYPE_MAPPER_VECTOR",
]
