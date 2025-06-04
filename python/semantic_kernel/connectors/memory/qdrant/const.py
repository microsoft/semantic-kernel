# Copyright (c) Microsoft. All rights reserved.

from qdrant_client.models import Datatype, Distance

from semantic_kernel.data.const import DistanceFunction

DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_SIMILARITY: Distance.COSINE,
    DistanceFunction.DOT_PROD: Distance.DOT,
    DistanceFunction.EUCLIDEAN_DISTANCE: Distance.EUCLID,
    DistanceFunction.MANHATTAN: Distance.MANHATTAN,
    "default": Distance.COSINE,
}

TYPE_MAPPER_VECTOR = {
    "float": Datatype.FLOAT32,
    "int": Datatype.UINT8,
    "binary": Datatype.UINT8,
    "default": Datatype.FLOAT32,
}

__all__ = [
    "DISTANCE_FUNCTION_MAP",
    "TYPE_MAPPER_VECTOR",
]
