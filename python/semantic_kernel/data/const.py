# Copyright (c) Microsoft. All rights reserved.


from enum import Enum


class IndexKind(str, Enum):
    """Index kinds for similarity search."""

    HNSW = "hnsw"
    FLAT = "flat"


class DistanceFunction(str, Enum):
    """Distance functions for similarity search."""

    COSINE = "cosine"
    DOT_PROD = "dot_prod"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
    HAMMING = "hamming"
