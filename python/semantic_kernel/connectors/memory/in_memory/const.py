# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Callable
from typing import Any

from numpy import dot
from scipy.spatial.distance import cityblock, cosine, euclidean, hamming, sqeuclidean

from semantic_kernel.data.const import DistanceFunction

DISTANCE_FUNCTION_MAP: dict[DistanceFunction | str, Callable[..., Any]] = {
    DistanceFunction.COSINE_DISTANCE: cosine,
    DistanceFunction.COSINE_SIMILARITY: cosine,
    DistanceFunction.EUCLIDEAN_DISTANCE: euclidean,
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: sqeuclidean,
    DistanceFunction.MANHATTAN: cityblock,
    DistanceFunction.HAMMING: hamming,
    DistanceFunction.DOT_PROD: dot,
    "default": cosine,
}
