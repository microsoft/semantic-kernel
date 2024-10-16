# Copyright (c) Microsoft. All rights reserved.


from typing import Any

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordDataField, VectorStoreRecordVectorField


def to_vector_index_policy_type(index_kind: IndexKind) -> str:
    """Converts the index kind to the vector index policy type for Azure Cosmos DB NoSQL container.

    Args:
        index_kind (IndexKind): The index kind.

    Returns:
        str: The vector index policy type.
    """
    match index_kind:
        case IndexKind.FLAT:
            return "flat"
        case IndexKind.QUANTIZED_FLAT:
            return "quantizedFlat"
        case IndexKind.DISK_ANN:
            return "diskANN"

    raise ValueError(f"Index kind '{index_kind}' is not supported by Azure Cosmos DB NoSQL container.")


def to_distance_function(distance_function: DistanceFunction) -> str:
    """Converts the distance function to the distance function for Azure Cosmos DB NoSQL container."""
    match distance_function:
        case DistanceFunction.COSINE:
            return "cosine"
        case DistanceFunction.DOT_PROD:
            return "dotproduct"
        case DistanceFunction.EUCLIDEAN:
            return "euclidean"

    raise ValueError(f"Distance function '{distance_function}' is not supported by Azure Cosmos DB NoSQL container.")


def create_default_indexing_policy(data_model_definition: VectorStoreRecordDefinition) -> dict[str, Any]:
    """Creates a default indexing policy for the Azure Cosmos DB NoSQL container.

    A default indexing policy is created based on the data model definition and has an automatic indexing policy.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The definition of the data model.

    Returns:
        dict[str, Any]: The indexing policy.
    """
    indexing_policy = {
        "automatic": True,
        "includedPaths": [
            {
                "path": "/*",
            }
        ],
        "excludedPaths": [
            {
                "path": '/"_etag"/?',
            }
        ],
        "vectorIndexes": [],
    }

    for _, field in data_model_definition.fields.items():
        if isinstance(field, VectorStoreRecordDataField) and (
            not field.is_full_text_searchable and not field.is_filterable
        ):
            indexing_policy["excludedPaths"].append({"path": f'/"{field.name}"/*'})

        if isinstance(field, VectorStoreRecordVectorField):
            indexing_policy["vectorIndexes"].append({
                "path": f'/"{field.name}"',
                "type": to_vector_index_policy_type(field.index_kind),
            })
            # Exclude the vector field from the index for performance optimization.
            indexing_policy["excludedPaths"].append({"path": f'/"{field.name}"/*'})

    return indexing_policy


def create_default_vector_embedding_policy(data_model_definition: VectorStoreRecordDefinition) -> dict[str, Any]:
    """Creates a default vector embedding policy for the Azure Cosmos DB NoSQL container.

    A default vector embedding policy is created based on the data model definition.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The definition of the data model.

    Returns:
        dict[str, Any]: The vector embedding policy.
    """
    vector_embedding_policy = {"vectorEmbeddings": []}

    for _, field in data_model_definition.fields.items():
        if isinstance(field, VectorStoreRecordVectorField):
            vector_embedding_policy["vectorEmbeddings"].append({
                "path": f'/"{field.name}"',
                "dataType": "float32",
                "distanceFunction": to_distance_function(field.distance_function),
                "dimensions": field.dimensions,
            })

    return vector_embedding_policy


def get_partition_key(key: str | AzureCosmosDBNoSQLCompositeKey) -> str:
    """Gets the partition key from the key.

    Args:
        key (str | AzureCosmosDBNoSQLCompositeKey): The key.

    Returns:
        str: The partition key.
    """
    if isinstance(key, AzureCosmosDBNoSQLCompositeKey):
        return key.partition_key

    return key
