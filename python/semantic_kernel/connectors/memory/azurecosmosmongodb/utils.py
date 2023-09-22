# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.memory.memory_record import MemoryRecord

SEARCH_FIELD_ID = "Id"
SEARCH_FIELD_TEXT = "Text"
SEARCH_FIELD_SRC = "ExternalSourceName"
SEARCH_FIELD_DESC = "Description"
SEARCH_FIELD_IS_REF = "IsReference"
DEFAULT_INSERT_BATCH_SIZE = 1000


def dict_to_memory_record(data: dict, embedding_key) -> MemoryRecord:
    """Converts a search result to a MemoryRecord.

    Arguments:
        data {dict} -- Azure CosmosDB MongoDB search data.

    Returns:
        MemoryRecord -- The MemoryRecord from Azure CosmosDB MongoDB Data Result.
    """

    sk_result = MemoryRecord(
        id=data[SEARCH_FIELD_ID],
        key=data[SEARCH_FIELD_ID],
        text=data[SEARCH_FIELD_TEXT],
        external_source_name=data[SEARCH_FIELD_SRC],
        description=data[SEARCH_FIELD_DESC],
        is_reference=data[SEARCH_FIELD_IS_REF],
        embedding=data[embedding_key],
        timestamp=None,
    )
    return sk_result


def memory_record_to_mongodb_record(record: MemoryRecord, embedding_key) -> dict:
    """Convert a MemoryRecord to a dictionary

    Arguments:
        record {MemoryRecord} -- The MemoryRecord from Azure CosmosDB MongoDB Data Result.

    Returns:
        data {dict} -- Dictionary data.
    """
    return {
        SEARCH_FIELD_ID: record._id,
        SEARCH_FIELD_TEXT: str(record._text),
        SEARCH_FIELD_SRC: record._external_source_name or "",
        SEARCH_FIELD_DESC: record._description or "",
        SEARCH_FIELD_IS_REF: record._is_reference,
        embedding_key: record._embedding.tolist(),
    }


def get_mongodb_resources(connection_string: str, database_name: str):
    """
    Connects to a MongoDB database using the given connection string and database name.

    Args:
        connection_string (str): The connection string for the MongoDB database.
        database_name (str): The name of the database to connect to.

    Returns:
        tuple: A tuple containing the MongoDB client and database objects.
    """
    try:
        import pymongo
    except ImportError as exc:
        raise ImportError(
            f"Could not import pymongo, please install it with `pip install pymongo`. {exc}"
        ) from exc

    try:
        client = pymongo.MongoClient(connection_string)
        database = client[database_name]
    except Exception as exc:
        raise Exception(f"Error while connecting to MongoDB: {exc}") from exc

    return client, database
