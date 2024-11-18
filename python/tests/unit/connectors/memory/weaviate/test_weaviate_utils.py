# Copyright (c) Microsoft. All rights reserved.


import pytest
from weaviate.collections.classes.config_vectorizers import VectorDistances

from semantic_kernel.connectors.memory.weaviate.utils import to_weaviate_vector_distance
from semantic_kernel.data.const import DistanceFunction


def test_distance_function_mapping() -> None:
    """Test the distance function mapping."""

    assert to_weaviate_vector_distance(DistanceFunction.COSINE_DISTANCE) == VectorDistances.COSINE
    assert to_weaviate_vector_distance(DistanceFunction.DOT_PROD) == VectorDistances.DOT
    assert to_weaviate_vector_distance(DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE) == VectorDistances.L2_SQUARED
    assert to_weaviate_vector_distance(DistanceFunction.MANHATTAN) == VectorDistances.MANHATTAN
    assert to_weaviate_vector_distance(DistanceFunction.HAMMING) == VectorDistances.HAMMING
    with pytest.raises(ValueError):
        to_weaviate_vector_distance(DistanceFunction.COSINE_SIMILARITY) is None
        to_weaviate_vector_distance(DistanceFunction.EUCLIDEAN_DISTANCE) is None
