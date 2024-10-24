# Copyright (c) Microsoft. All rights reserved.


from weaviate.collections.classes.config_vectorizers import VectorDistances

from semantic_kernel.connectors.memory.weaviate.utils import to_weaviate_vector_distance
from semantic_kernel.data.const import DistanceFunction


def test_distance_function_mapping() -> None:
    """Test the distance function mapping."""

    assert to_weaviate_vector_distance(DistanceFunction.COSINE) == VectorDistances.COSINE
    assert to_weaviate_vector_distance(DistanceFunction.DOT_PROD) == VectorDistances.DOT
    assert to_weaviate_vector_distance(DistanceFunction.EUCLIDEAN) == VectorDistances.L2_SQUARED
    assert to_weaviate_vector_distance(DistanceFunction.MANHATTAN) == VectorDistances.MANHATTAN
    assert to_weaviate_vector_distance(DistanceFunction.HAMMING) == VectorDistances.HAMMING
