# Copyright (c) Microsoft. All rights reserved.


from enum import Enum

from semantic_kernel.data.const import DistanceFunction


class RedisCollectionTypes(str, Enum):
    JSON = "json"
    HASHSET = "hashset"


DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE: "COSINE",
    DistanceFunction.DOT_PROD: "IP",
    DistanceFunction.EUCLIDEAN: "L2",
    "default": "COSINE",
}

TYPE_MAPPER_VECTOR = {
    "list[float]": "FLOAT32",
    "list[int]": "FLOAT16",
    "list[binary]": "FLOAT16",
    "default": "FLOAT32",
}

__all__ = [
    "DISTANCE_FUNCTION_MAP",
    "TYPE_MAPPER_VECTOR",
]
