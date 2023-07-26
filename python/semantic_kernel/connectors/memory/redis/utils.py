# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime
from typing import Any, Dict
import numpy as np

import redis
from redis import Redis
from redis.commands.search.document import Document
from semantic_kernel.memory.memory_record import MemoryRecord

def redis_key(collection_name: str, key: str) -> str:
    """
    Returns the Redis key for an element called key within collection_name

    Arguments:
        collection_name {str} -- Name for a collection of embeddings
        key {str} -- ID associated with a memory record

    Returns:
        str -- Redis key in the format collection_name:key
    """
    return f"{collection_name}:{key}"

def serialize_record_to_redis(record: MemoryRecord, vector_type: np.dtype) -> Dict[str, Any]:
    mapping = {
        "timestamp": record._timestamp.isoformat() if record._timestamp else "",
        "is_reference": 1 if record._is_reference else 0,
        "external_source_name": record._external_source_name or "",
        "id": record._id or "",
        "description": record._description or "",
        "text": record._text or "",
        "additional_metadata": record._additional_metadata or "",
        "embedding": (
            record._embedding.astype(vector_type).tobytes()
            if record._embedding is not None
            else ""
        ),
    }
    return mapping

def deserialize_redis_to_record(fields: Dict[str, Any], vector_type: np.dtype, with_embedding: bool) -> MemoryRecord:
    record = MemoryRecord(
        id=fields[b"id"].decode(),
        is_reference=bool(int(fields[b"is_reference"].decode())),
        external_source_name=fields[b"external_source_name"].decode(),
        description=fields[b"description"].decode(),
        text=fields[b"text"].decode(),
        additional_metadata=fields[b"additional_metadata"].decode(),
        embedding=None,
    )

    if fields[b"timestamp"] != b"":
        record._timestamp = datetime.fromisoformat(fields[b"timestamp"].decode())

    if with_embedding:
        # Extract using the vector type, then convert to regular Python float type
        record._embedding = np.frombuffer(fields[b"embedding"], dtype=vector_type).astype(float)

    return record

def deserialize_document_to_record(database: Redis, doc: Document, vector_type: np.dtype, with_embedding: bool) -> MemoryRecord:
    # Parse collection name out of ID
    key_str = doc["id"]
    colon_index = key_str.index(":")
    id_str = key_str[colon_index + 1 :]

    record = MemoryRecord.local_record(
        id=id_str,
        text=doc["text"],
        description=doc["description"],
        additional_metadata=doc["additional_metadata"],
        embedding=None,
        timestamp=None,
    )

    if doc["timestamp"] != "":
        record._timestamp = datetime.fromisoformat(doc["timestamp"])

    if with_embedding:
        # Some bytes are lost when retrieving a document, fetch raw embedding
        eb = database.hget(key_str, "embedding")
        record._embedding = np.frombuffer(eb, dtype=vector_type).astype(float)

    return record


