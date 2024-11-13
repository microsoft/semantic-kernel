# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.data.const import DistanceFunction, IndexKind

# The name of the property that will be used as the item id in Azure Cosmos DB NoSQL
COSMOS_ITEM_ID_PROPERTY_NAME = "id"

INDEX_KIND_MAPPING = {
    IndexKind.FLAT: "flat",
    IndexKind.QUANTIZED_FLAT: "quantizedFlat",
    IndexKind.DISK_ANN: "diskANN",
}

DISTANCE_FUNCTION_MAPPING = {
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.DOT_PROD: "dotproduct",
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
}

DATATYPES_MAPPING = {
    "default": "float32",
    "float": "float32",
    "list[float]": "float32",
    "int": "int32",
    "list[int]": "int32",
}
