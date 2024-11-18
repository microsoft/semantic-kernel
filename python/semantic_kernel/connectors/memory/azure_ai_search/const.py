# Copyright (c) Microsoft. All rights reserved.

from azure.search.documents.indexes.models import (
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchFieldDataType,
    VectorSearchAlgorithmMetric,
)

from semantic_kernel.data.const import DistanceFunction, IndexKind

INDEX_ALGORITHM_MAP = {
    IndexKind.HNSW: (HnswAlgorithmConfiguration, HnswParameters),
    IndexKind.FLAT: (ExhaustiveKnnAlgorithmConfiguration, ExhaustiveKnnParameters),
    "default": (HnswAlgorithmConfiguration, HnswParameters),
}

DISTANCE_FUNCTION_MAP = {
    DistanceFunction.COSINE_DISTANCE: VectorSearchAlgorithmMetric.COSINE,
    DistanceFunction.DOT_PROD: VectorSearchAlgorithmMetric.DOT_PRODUCT,
    DistanceFunction.EUCLIDEAN_DISTANCE: VectorSearchAlgorithmMetric.EUCLIDEAN,
    DistanceFunction.HAMMING: VectorSearchAlgorithmMetric.HAMMING,
    "default": VectorSearchAlgorithmMetric.COSINE,
}

TYPE_MAPPER_DATA = {
    "str": SearchFieldDataType.String,
    "int": SearchFieldDataType.Int64,
    "float": SearchFieldDataType.Double,
    "bool": SearchFieldDataType.Boolean,
    "list[str]": SearchFieldDataType.Collection(SearchFieldDataType.String),
    "list[int]": SearchFieldDataType.Collection(SearchFieldDataType.Int64),
    "list[float]": SearchFieldDataType.Collection(SearchFieldDataType.Double),
    "list[bool]": SearchFieldDataType.Collection(SearchFieldDataType.Boolean),
    "default": SearchFieldDataType.String,
}

TYPE_MAPPER_VECTOR = {
    "float": SearchFieldDataType.Collection(SearchFieldDataType.Single),
    "int": "Collection(Edm.Int16)",
    "binary": "Collection(Edm.Byte)",
    "default": SearchFieldDataType.Collection(SearchFieldDataType.Single),
}

__all__ = [
    "DISTANCE_FUNCTION_MAP",
    "INDEX_ALGORITHM_MAP",
    "TYPE_MAPPER_DATA",
    "TYPE_MAPPER_VECTOR",
]
