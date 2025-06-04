# Copyright (c) Microsoft. All rights reserved.

import operator
from collections.abc import Callable
from enum import Enum
from typing import Final


class IndexKind(str, Enum):
    """Index kinds for similarity search.

    HNSW
        Hierarchical Navigable Small World which performs an approximate nearest neighbor (ANN) search.
        Lower accuracy than exhaustive k nearest neighbor, but faster and more efficient.

    Flat
        Does a brute force search to find the nearest neighbors.
        Calculates the distances between all pairs of data points, so has a linear time complexity,
        that grows directly proportional to the number of points.
        Also referred to as exhaustive k nearest neighbor in some databases.
        High recall accuracy, but slower and more expensive than HNSW.
        Better with smaller datasets.

    IVF Flat
        Inverted File with Flat Compression.
        Designed to enhance search efficiency by narrowing the search area
        through the use of neighbor partitions or clusters.
        Also referred to as approximate nearest neighbor (ANN) search.

    Disk ANN
        Disk-based Approximate Nearest Neighbor algorithm designed for efficiently searching
        for approximate nearest neighbors (ANN) in high-dimensional spaces.
        The primary focus of DiskANN is to handle large-scale datasets that cannot fit entirely
        into memory, leveraging disk storage to store the data while maintaining fast search times.

    Quantized Flat
        Index that compresses vectors using DiskANN-based quantization methods for better efficiency in the kNN search.

    Dynamic
        Dynamic index allows to automatically switch from FLAT to HNSW indexes.

    """

    HNSW = "hnsw"
    FLAT = "flat"
    IVF_FLAT = "ivf_flat"
    DISK_ANN = "disk_ann"
    QUANTIZED_FLAT = "quantized_flat"
    DYNAMIC = "dynamic"


class DistanceFunction(str, Enum):
    """Distance functions for similarity search.

    Cosine Similarity
        the cosine (angular) similarity between two vectors
        measures only the angle between the two vectors, without taking into account the length of the vectors
        Cosine Similarity = 1 - Cosine Distance
        -1 means vectors are opposite
        0 means vectors are orthogonal
        1 means vectors are identical
    Cosine Distance
        the cosine (angular) distance between two vectors
        measures only the angle between the two vectors, without taking into account the length of the vectors
        Cosine Distance = 1 - Cosine Similarity
        2 means vectors are opposite
        1 means vectors are orthogonal
        0 means vectors are identical
    Dot Product
        measures both the length and angle between two vectors
        same as cosine similarity if the vectors are the same length, but more performant
    Euclidean Distance
        measures the Euclidean distance between two vectors
        also known as l2-norm
    Euclidean Squared Distance
        measures the Euclidean squared distance between two vectors
        also known as l2-squared
    Manhattan
        measures the Manhattan distance between two vectors
    Hamming
        number of differences between vectors at each dimensions
    """

    COSINE_SIMILARITY = "cosine_similarity"
    COSINE_DISTANCE = "cosine_distance"
    DOT_PROD = "dot_prod"
    EUCLIDEAN_DISTANCE = "euclidean_distance"
    EUCLIDEAN_SQUARED_DISTANCE = "euclidean_squared_distance"
    MANHATTAN = "manhattan"
    HAMMING = "hamming"


DISTANCE_FUNCTION_DIRECTION_HELPER: Final[dict[DistanceFunction, Callable[[int | float, int | float], bool]]] = {
    DistanceFunction.COSINE_SIMILARITY: operator.gt,
    DistanceFunction.COSINE_DISTANCE: operator.le,
    DistanceFunction.DOT_PROD: operator.gt,
    DistanceFunction.EUCLIDEAN_DISTANCE: operator.le,
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: operator.le,
    DistanceFunction.MANHATTAN: operator.le,
    DistanceFunction.HAMMING: operator.le,
}
DEFAULT_FUNCTION_NAME: Final[str] = "search"
DEFAULT_DESCRIPTION: Final[str] = (
    "Perform a search for content related to the specified query and return string results"
)


class TextSearchFunctions(str, Enum):
    """Text search functions.

    Attributes:
        SEARCH: Search using a query.
        GET_TEXT_SEARCH_RESULT: Get text search results.
        GET_SEARCH_RESULT: Get search results.
    """

    SEARCH = "search"
    GET_TEXT_SEARCH_RESULT = "get_text_search_result"
    GET_SEARCH_RESULT = "get_search_result"
