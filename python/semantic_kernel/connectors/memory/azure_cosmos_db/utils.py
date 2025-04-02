# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
from typing import Any

from azure.cosmos.aio import CosmosClient

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.connectors.memory.azure_cosmos_db.const import (
    DATATYPES_MAPPING,
    DISTANCE_FUNCTION_MAPPING,
    INDEX_KIND_MAPPING,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreModelException


def to_vector_index_policy_type(index_kind: IndexKind | None) -> str:
    """Converts the index kind to the vector index policy type for Azure Cosmos DB NoSQL container.

    Depending on the index kind, the maximum number of dimensions may be limited:
    https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search#vector-indexing-policies

    Args:
        index_kind (IndexKind): The index kind.

    Returns:
        str: The vector index policy type.

    Raises:
        VectorStoreModelException: If the index kind is not supported by Azure Cosmos DB NoSQL container.
    """
    if index_kind is None:
        # Use IndexKind.FLAT as the default index kind.
        return INDEX_KIND_MAPPING[IndexKind.FLAT]

    if index_kind in INDEX_KIND_MAPPING:
        return INDEX_KIND_MAPPING[index_kind]

    raise VectorStoreModelException(f"Index kind '{index_kind}' is not supported by Azure Cosmos DB NoSQL container.")


def to_distance_function(distance_function: DistanceFunction | None) -> str:
    """Converts the distance function to the distance function for Azure Cosmos DB NoSQL container.

    Args:
        distance_function: The distance function.

    Returns:
        str: The distance function as defined by Azure Cosmos DB NoSQL container.

    Raises:
        VectorStoreModelException: If the distance function is not supported by Azure Cosmos DB NoSQL container.

    """
    if distance_function is None:
        # Use DistanceFunction.COSINE_SIMILARITY as the default distance function.
        return DISTANCE_FUNCTION_MAPPING[DistanceFunction.COSINE_SIMILARITY]

    if distance_function in DISTANCE_FUNCTION_MAPPING:
        return DISTANCE_FUNCTION_MAPPING[distance_function]

    raise VectorStoreModelException(
        f"Distance function '{distance_function}' is not supported by Azure Cosmos DB NoSQL container."
    )


def to_datatype(property_type: str | None) -> str:
    """Converts the property type to the data type for Azure Cosmos DB NoSQL container.

    Args:
        property_type: The property type.

    Returns:
        str: The data type as defined by Azure Cosmos DB NoSQL container.

    Raises:
        VectorStoreModelException: If the property type is not supported by Azure Cosmos DB NoSQL container

    """
    if property_type is None:
        # Use the default data type.
        return DATATYPES_MAPPING["default"]

    if property_type in DATATYPES_MAPPING:
        return DATATYPES_MAPPING[property_type]

    raise VectorStoreModelException(
        f"Property type '{property_type}' is not supported by Azure Cosmos DB NoSQL container."
    )


def create_default_indexing_policy(data_model_definition: VectorStoreRecordDefinition) -> dict[str, Any]:
    """Creates a default indexing policy for the Azure Cosmos DB NoSQL container.

    A default indexing policy is created based on the data model definition and has an automatic indexing policy.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The definition of the data model.

    Returns:
        dict[str, Any]: The indexing policy.

    Raises:
        VectorStoreModelException: If the field is not full text searchable and not filterable.
    """
    indexing_policy: dict[str, Any] = {
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

    Raises:
        VectorStoreModelException: If the datatype or distance function is not supported by Azure Cosmos DB NoSQL.

    """
    vector_embedding_policy: dict[str, Any] = {"vectorEmbeddings": []}

    for _, field in data_model_definition.fields.items():
        if isinstance(field, VectorStoreRecordVectorField):
            vector_embedding_policy["vectorEmbeddings"].append({
                "path": f'/"{field.name}"',
                "dataType": to_datatype(field.property_type),
                "distanceFunction": to_distance_function(field.distance_function),
                "dimensions": field.dimensions,
            })

    return vector_embedding_policy


def get_key(key: str | AzureCosmosDBNoSQLCompositeKey) -> str:
    """Gets the key value from the key.

    Args:
        key (str | AzureCosmosDBNoSQLCompositeKey): The key.

    Returns:
        str: The key.
    """
    if isinstance(key, AzureCosmosDBNoSQLCompositeKey):
        return key.key

    return key


def get_partition_key(key: str | AzureCosmosDBNoSQLCompositeKey) -> str:
    """Gets the partition key value from the key.

    Args:
        key (str | AzureCosmosDBNoSQLCompositeKey): The key.

    Returns:
        str: The partition key.
    """
    if isinstance(key, AzureCosmosDBNoSQLCompositeKey):
        return key.partition_key

    return key


class CosmosClientWrapper(CosmosClient):
    """Wrapper to make sure the CosmosClient is closed properly."""

    def __del__(self) -> None:
        """Close the CosmosClient."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())
