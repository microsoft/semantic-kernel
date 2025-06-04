# Copyright (c) Microsoft. All rights reserved.

from typing import Final

from semantic_kernel.data.const import DistanceFunction

DISTANCE_FUNCTION_MAPPING: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.DOT_PROD: "dotProduct",
}

MONGODB_ID_FIELD: Final[str] = "_id"
MONGODB_SCORE_FIELD: Final[str] = "score"
DEFAULT_DB_NAME = "default"
DEFAULT_SEARCH_INDEX_NAME = "default"
