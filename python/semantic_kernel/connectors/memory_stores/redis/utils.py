# Copyright (c) Microsoft. All rights reserved.

import json
from datetime import datetime
from typing import Any

import numpy as np
from redis.asyncio.client import Redis
from redis.commands.search.document import Document

from semantic_kernel.memory.memory_record import MemoryRecord


def get_redis_key(collection_name: str, record_id: str) -> str:  # pragma: no cover
    """Returns the Redis key for an element called record_id within collection_name.

    Args:
        collection_name (str): Name for a collection of embeddings
        record_id (str): ID associated with a memory record

    Returns:
        str: Redis key in the format collection_name:id
    """
    return f"{collection_name}:{record_id}"


def split_redis_key(redis_key: str) -> tuple[str, str]:  # pragma: no cover
    """Split a Redis key into its collection name and record ID.

    Args:
        redis_key (str): Redis key

    Returns:
        tuple[str, str]: Tuple of the collection name and ID
    """
    collection, record_id = redis_key.split(":")
    return collection, record_id


def serialize_record_to_redis(record: MemoryRecord, vector_type: np.dtype) -> dict[str, Any]:  # pragma: no cover
    """Serialize a MemoryRecord to Redis fields."""
    all_metadata = {
        "is_reference": record._is_reference,
        "external_source_name": record._external_source_name or "",
        "id": record._id or "",
        "description": record._description or "",
        "text": record._text or "",
        "additional_metadata": record._additional_metadata or "",
    }

    return {
        "key": record._key or "",
        "timestamp": record._timestamp.isoformat() if record._timestamp else "",
        "metadata": json.dumps(all_metadata),
        "embedding": (record._embedding.astype(vector_type).tobytes() if record._embedding is not None else ""),
    }


def deserialize_redis_to_record(
    fields: dict[str, Any], vector_type: np.dtype, with_embedding: bool
) -> MemoryRecord:  # pragma: no cover
    """Deserialize Redis fields to a MemoryRecord."""
    metadata = json.loads(fields[b"metadata"])
    record = MemoryRecord(
        id=metadata["id"],
        is_reference=metadata["is_reference"] is True,
        description=metadata["description"],
        external_source_name=metadata["external_source_name"],
        text=metadata["text"],
        additional_metadata=metadata["additional_metadata"],
        embedding=None,
    )

    if fields[b"timestamp"] != b"":
        record._timestamp = datetime.fromisoformat(fields[b"timestamp"].decode())

    if with_embedding:
        # Extract using the vector type, then convert to regular Python float type
        record._embedding = np.frombuffer(fields[b"embedding"], dtype=vector_type).astype(float)

    return record


def deserialize_document_to_record(
    database: Redis, doc: Document, vector_type: np.dtype, with_embedding: bool
) -> MemoryRecord:  # pragma: no cover
    """Deserialize document to a MemoryRecord."""
    # Document's ID refers to the Redis key
    redis_key = doc["id"]
    _, id_str = split_redis_key(redis_key)

    metadata = json.loads(doc["metadata"])
    record = MemoryRecord(
        id=id_str,
        is_reference=metadata["is_reference"] is True,
        description=metadata["description"],
        external_source_name=metadata["external_source_name"],
        text=metadata["text"],
        additional_metadata=metadata["additional_metadata"],
        embedding=None,
    )

    if doc["timestamp"] != "":
        record._timestamp = datetime.fromisoformat(doc["timestamp"])

    if with_embedding:
        # Some bytes are lost when retrieving a document, fetch raw embedding
        eb = database.hget(redis_key, "embedding")
        record._embedding = np.frombuffer(eb, dtype=vector_type).astype(float)

    return record
