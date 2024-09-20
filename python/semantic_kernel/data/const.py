# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Final

DEFAULT_DESCRIPTION: Final[str] = (
    "Perform a search for content related to the specified query and return string results"
)
DEFAULT_COUNT: Final[int] = 5


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
