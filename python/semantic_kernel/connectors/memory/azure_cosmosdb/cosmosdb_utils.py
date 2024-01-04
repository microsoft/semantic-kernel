# Copyright (c) Microsoft. All rights reserved.

from pymongo import MongoClient


def get_mongodb_resources(connection_string: str, database_name: str):
    try:
        client = MongoClient(connection_string)
        database = client[database_name]
    except Exception as ex:
        raise Exception(
            f"Error while connecting to Azure Cosmos MongoDb vCore: {ex}"
        ) from ex
    return client, database
