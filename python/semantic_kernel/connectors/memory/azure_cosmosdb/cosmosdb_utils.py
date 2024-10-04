# Copyright (c) Microsoft. All rights reserved.
import os

from dotenv import load_dotenv
from pymongo import MongoClient

from semantic_kernel.exceptions import ServiceInitializationError


def get_mongodb_search_client(connection_string: str):
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
        return MongoClient(cosmos_conn_str)

    raise ServiceInitializationError("Error: unable to create Azure Cosmos Mongo vCore Vector DB client.")
