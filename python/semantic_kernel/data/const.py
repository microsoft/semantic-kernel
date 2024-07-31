# Copyright (c) Microsoft. All rights reserved.


from enum import Enum


class IndexKind(str, Enum):
    HNSW = "hnsw"
    FLAT = "flat"


class DistanceFunction(str, Enum):
    COSINE = "cosine"
    DOT_PROD = "dot_prod"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
