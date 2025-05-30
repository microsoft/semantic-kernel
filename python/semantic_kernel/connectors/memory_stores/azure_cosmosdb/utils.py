# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class CosmosDBSimilarityType(str, Enum):
    """Cosmos DB Similarity Type as enumerator."""

    COS = "COS"
    """CosineSimilarity"""
    IP = "IP"
    """inner - product"""
    L2 = "L2"
    """Euclidean distance"""


@experimental
class CosmosDBVectorSearchType(str, Enum):
    """Cosmos DB Vector Search Type as enumerator."""

    VECTOR_IVF = "vector-ivf"
    """IVF vector index"""
    VECTOR_HNSW = "vector-hnsw"
    """HNSW vector index"""
