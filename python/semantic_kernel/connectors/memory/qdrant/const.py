# Copyright (c) Microsoft. All rights reserved.

from qdrant_client.models import Datatype, Distance

from semantic_kernel.data.models.vector_store_record_fields import DistanceFunction

DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE: Distance.COSINE,
    DistanceFunction.DOT_PROD: Distance.DOT,
    DistanceFunction.EUCLIDEAN: Distance.EUCLID,
    DistanceFunction.MANHATTAN: Distance.MANHATTAN,
    "default": Distance.COSINE,
}

TYPE_MAPPER_VECTOR = {
    "list[float]": Datatype.FLOAT32,
    "list[int]": Datatype.UINT8,
    "list[binary]": Datatype.UINT8,
    "default": Datatype.FLOAT32,
}

__all__ = [
    "DISTANCE_FUNCTION_MAP",
    "TYPE_MAPPER_VECTOR",
]
