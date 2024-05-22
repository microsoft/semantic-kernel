# Copyright (c) Microsoft. All rights reserved.
import os
from enum import Enum

from dotenv import load_dotenv
from pymongo import MongoClient

from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_function


@experimental_function
class CosmosDBSimilarityType(str, Enum):
    """Cosmos DB Similarity Type as enumerator."""

    COS = "COS"
    """CosineSimilarity"""
    IP = "IP"
    """inner - product"""
    L2 = "L2"
    """Euclidean distance"""


@experimental_function
class CosmosDBVectorSearchType(str, Enum):
    """Cosmos DB Vector Search Type as enumerator."""

    VECTOR_IVF = "vector-ivf"
    """IVF vector index"""
    VECTOR_HNSW = "vector-hnsw"
    """HNSW vector index"""


@experimental_function
def get_mongodb_search_client(connection_string: str, application_name: str):
    """
    Returns a client for Azure Cosmos Mongo vCore Vector DB

    Arguments:
        connection_string {str}

    """

    ENV_VAR_COSMOS_CONN_STR = "AZCOSMOS_CONNSTR"

    load_dotenv()

    # Cosmos connection string
    if connection_string:
        cosmos_conn_str = connection_string
    elif os.getenv(ENV_VAR_COSMOS_CONN_STR):
        cosmos_conn_str = os.getenv(ENV_VAR_COSMOS_CONN_STR)
    else:
        raise ServiceInitializationError("Error: missing Azure Cosmos Mongo vCore Connection String")

    if cosmos_conn_str:
        app_name = application_name if application_name is not None else HTTP_USER_AGENT
        return MongoClient(cosmos_conn_str, appname=app_name)

    raise ServiceInitializationError("Error: unable to create Azure Cosmos Mongo vCore Vector DB client.")
