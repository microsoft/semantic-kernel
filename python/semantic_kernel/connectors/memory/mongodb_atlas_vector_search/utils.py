# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from numpy import array
from pymongo.operations import SearchIndexModel
from semantic_kernel.memory.memory_record import MemoryRecord

_DEFAULT_DIMENSIONS = 384
_DEFAULT_SIMILARITY = "dotProduct"
_DEFAULT_TYPE = "knnVector"
_DEFAULT_SEARCH_INDEX_NAME = "atlas_vector_search_index"

# see: https://www.mongodb.com/docs/atlas/atlas-search/field-types/knn-vector/#configure-fts-field-type-field-properties
_MAX_DIMENSIONS = 2048
_SIMILARITY_OPTIONS = [
    "euclidean",
    "cosine",
    "dotProduct",
]

MONGODB_FIELD_ID = "MemoryId"
MONGODB_FIELD_TEXT = "Text"
MONGODB_FIELD_EMBEDDING = "MemoryRecordEmbedding"
MONGODB_FIELD_SRC = "ExternalSourceName"
MONGODB_FIELD_DESC = "Description"
MONGODB_FIELD_METADATA = "AdditionalMetadata"
MONGODB_FIELD_IS_REF = "IsReference"
MONGODB_FIELD_KEY = "Key"
MONGODB_FIELD_TIMESTAMP = "timestamp"


def generate_search_index_model(
    dimensions: int | None, similarity: str | None
) -> SearchIndexModel:
    """Generates a search model index object given dimesions and similarity"""
    dimensions = dimensions or _DEFAULT_DIMENSIONS
    similarity = similarity or _DEFAULT_SIMILARITY
    if (
        dimensions > _MAX_DIMENSIONS
        or dimensions < 1
        or not isinstance(dimensions, int)
    ):
        raise ValueError(
            f"Invalid dimension provided {dimensions}; must be an int between 1 and {_MAX_DIMENSIONS}"
        )
    if similarity not in _SIMILARITY_OPTIONS:
        raise ValueError(
            f"Invalid similarity {similarity} provided; must be any of these {_SIMILARITY_OPTIONS} types"
        )

    return SearchIndexModel(
        {
            "mappings": {
                "dynamic": True,
                "fields": {
                    MONGODB_FIELD_EMBEDDING: {
                        "dimensions": dimensions,
                        "similarity": similarity,
                        "type": _DEFAULT_TYPE,
                    }
                },
            }
        },
        name=_DEFAULT_SEARCH_INDEX_NAME,
    )


def document_to_memory_record(data: dict, with_embeddings: bool) -> MemoryRecord:
    """Converts a search result to a MemoryRecord.

    Arguments:
        data {dict} -- Azure Cognitive Search result data.

    Returns:
        MemoryRecord -- The MemoryRecord from Azure Cognitive Search Data Result.
    """

    return MemoryRecord(
        id=data.get(MONGODB_FIELD_ID),
        text=data.get(MONGODB_FIELD_TEXT),
        external_source_name=data.get(MONGODB_FIELD_SRC),
        description=data.get(MONGODB_FIELD_DESC),
        additional_metadata=data.get(MONGODB_FIELD_METADATA),
        is_reference=data.get(MONGODB_FIELD_IS_REF),
        embedding=array(data.get(MONGODB_FIELD_EMBEDDING)) if with_embeddings else None,
        timestamp=data.get(MONGODB_FIELD_TIMESTAMP),
    )


def memory_record_to_mongo_document(record: MemoryRecord) -> dict:
    """Convert a MemoryRecord to a dictionary

    Arguments:
        record {MemoryRecord} -- The MemoryRecord from Azure Cognitive Search Data Result.

    Returns:
        data {dict} -- Dictionary data.
    """

    return {
        MONGODB_FIELD_ID: record._id,
        MONGODB_FIELD_TEXT: record._text,
        MONGODB_FIELD_SRC: record._external_source_name or "",
        MONGODB_FIELD_DESC: record._description or "",
        MONGODB_FIELD_METADATA: record._additional_metadata or "",
        MONGODB_FIELD_IS_REF: record._is_reference,
        MONGODB_FIELD_EMBEDDING: record._embedding.tolist(),
        MONGODB_FIELD_TIMESTAMP: record._timestamp,
    }
