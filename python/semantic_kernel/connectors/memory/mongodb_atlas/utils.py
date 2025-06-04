# Copyright (c) Microsoft. All rights reserved.

from numpy import array
from pymongo.operations import SearchIndexModel

from semantic_kernel.connectors.memory.mongodb_atlas.const import DISTANCE_FUNCTION_MAPPING
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord

NUM_CANDIDATES_SCALAR = 10

MONGODB_FIELD_ID = "_id"
MONGODB_FIELD_TEXT = "text"
MONGODB_FIELD_EMBEDDING = "embedding"
MONGODB_FIELD_SRC = "externalSourceName"
MONGODB_FIELD_DESC = "description"
MONGODB_FIELD_METADATA = "additionalMetadata"
MONGODB_FIELD_IS_REF = "isReference"
MONGODB_FIELD_KEY = "key"
MONGODB_FIELD_TIMESTAMP = "timestamp"


def document_to_memory_record(data: dict, with_embeddings: bool) -> MemoryRecord:
    """Converts a search result to a MemoryRecord.

    Args:
        data (dict): Azure Cognitive Search result data.
        with_embeddings (bool): Whether to include embeddings.

    Returns:
        MemoryRecord: The MemoryRecord from Azure Cognitive Search Data Result.
    """
    meta = data.get(MONGODB_FIELD_METADATA, {})

    return MemoryRecord(
        id=meta.get(MONGODB_FIELD_ID),
        text=meta.get(MONGODB_FIELD_TEXT),
        external_source_name=meta.get(MONGODB_FIELD_SRC),
        description=meta.get(MONGODB_FIELD_DESC),
        additional_metadata=meta.get(MONGODB_FIELD_METADATA),
        is_reference=meta.get(MONGODB_FIELD_IS_REF),
        embedding=array(data.get(MONGODB_FIELD_EMBEDDING)) if with_embeddings else None,
        timestamp=data.get(MONGODB_FIELD_TIMESTAMP),
        key=meta.get(MONGODB_FIELD_ID),
    )


def memory_record_to_mongo_document(record: MemoryRecord) -> dict:
    """Convert a MemoryRecord to a dictionary.

    Args:
        record (MemoryRecord): The MemoryRecord from Azure Cognitive Search Data Result.

    Returns:
        data (dict): Dictionary data.
    """
    return {
        MONGODB_FIELD_ID: record._id,
        MONGODB_FIELD_METADATA: {
            MONGODB_FIELD_ID: record._id,
            MONGODB_FIELD_TEXT: record._text,
            MONGODB_FIELD_SRC: record._external_source_name or "",
            MONGODB_FIELD_DESC: record._description or "",
            MONGODB_FIELD_METADATA: record._additional_metadata or "",
            MONGODB_FIELD_IS_REF: record._is_reference,
        },
        MONGODB_FIELD_EMBEDDING: record._embedding.tolist(),
        MONGODB_FIELD_TIMESTAMP: record._timestamp,
    }


def create_vector_field(field: VectorStoreRecordVectorField) -> dict:
    """Create a vector field.

    Args:
        field (VectorStoreRecordVectorField): The vector field.

    Returns:
        dict: The vector field.
    """
    if field.distance_function not in DISTANCE_FUNCTION_MAPPING:
        raise ServiceInitializationError(f"Invalid distance function: {field.distance_function}")
    return {
        "type": "vector",
        "numDimensions": field.dimensions,
        "path": field.name,
        "similarity": DISTANCE_FUNCTION_MAPPING[field.distance_function],
    }


def create_index_definition(record_definition: VectorStoreRecordDefinition, index_name: str) -> SearchIndexModel:
    """Create an index definition.

    Args:
        record_definition (VectorStoreRecordDefinition): The record definition.
        index_name (str): The index name.

    Returns:
        SearchIndexModel: The index definition.
    """
    vector_fields = [create_vector_field(field) for field in record_definition.vector_fields]
    data_fields = [
        {"path": field.name, "type": "filter"}
        for field in record_definition.fields
        if isinstance(field, VectorStoreRecordDataField) and (field.is_filterable or field.is_full_text_searchable)
    ]
    key_field = [{"path": record_definition.key_field.name, "type": "filter"}]
    return SearchIndexModel(
        type="vectorSearch", name=index_name, definition={"fields": vector_fields + data_fields + key_field}
    )
