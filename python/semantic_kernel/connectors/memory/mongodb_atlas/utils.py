# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import time

from motor.core import AgnosticDatabase
from numpy import array
from pymongo.operations import SearchIndexModel

from semantic_kernel.memory.memory_record import MemoryRecord

_DEFAULT_DIMENSIONS = 384
_DEFAULT_SIMILARITY = "dotProduct"
_DEFAULT_TYPE = "knnVector"
DEFAULT_SEARCH_INDEX_NAME = "default"
DEFAULT_DB_NAME = "default"

# see: https://www.mongodb.com/docs/atlas/atlas-search/field-types/knn-vector/#configure-fts-field-type-field-properties
_MAX_DIMENSIONS = 2048
_SIMILARITY_OPTIONS = [
    "euclidean",
    "cosine",
    "dotProduct",
]

MONGODB_FIELD_ID = "_id"
MONGODB_FIELD_TEXT = "text"
MONGODB_FIELD_EMBEDDING = "embedding"
MONGODB_FIELD_SRC = "externalSourceName"
MONGODB_FIELD_DESC = "description"
MONGODB_FIELD_METADATA = "additionalMetadata"
MONGODB_FIELD_IS_REF = "isReference"
MONGODB_FIELD_KEY = "key"
MONGODB_FIELD_TIMESTAMP = "timestamp"


def _is_queryable(indices) -> bool:
    return indices and indices[0].get("queryable") is True


async def wait_for_search_index_ready(
    database: AgnosticDatabase,
    collection_name: str,
    index_name: str = DEFAULT_SEARCH_INDEX_NAME,
    timeout: float = 60.0,
    poll_interval: float = 1.0,
) -> None:
    """Wait for a search index to be ready."""
    wait_time = timeout

    while not _is_queryable(
        await database[collection_name]
        .list_search_indexes(index_name)
        .to_list(length=1)
    ):
        if wait_time <= 0:
            raise TimeoutError(f"Index unavailable after waiting {timeout} seconds")
        time.sleep(poll_interval)
        wait_time -= poll_interval


def generate_search_index_model(
    dimensions: int | None = None, similarity: str | None = None
) -> SearchIndexModel:
    """Generates a search model index object given dimensions and similarity"""
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
        name=DEFAULT_SEARCH_INDEX_NAME,
    )


def document_to_memory_record(data: dict, with_embeddings: bool) -> MemoryRecord:
    """Converts a search result to a MemoryRecord.

    Arguments:
        data {dict} -- Azure Cognitive Search result data.

    Returns:
        MemoryRecord -- The MemoryRecord from Azure Cognitive Search Data Result.
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
