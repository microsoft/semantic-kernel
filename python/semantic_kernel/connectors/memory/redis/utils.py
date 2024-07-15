# Copyright (c) Microsoft. All rights reserved.

import json
from datetime import datetime
from typing import Any

import numpy as np
from redis import Redis
from redis.commands.search.document import Document
from redis.commands.search.field import Field as RedisField
from redis.commands.search.field import TextField, VectorField

from semantic_kernel.connectors.memory.azure_ai_search.const import DISTANCE_FUNCTION_MAP
from semantic_kernel.connectors.memory.redis.const import TYPE_MAPPER_VECTOR
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordVectorField,
)
from semantic_kernel.memory.memory_record import MemoryRecord


def get_redis_key(collection_name: str, record_id: str) -> str:
    """Returns the Redis key for an element called record_id within collection_name.

    Args:
        collection_name (str): Name for a collection of embeddings
        record_id (str): ID associated with a memory record

    Returns:
        str: Redis key in the format collection_name:id
    """
    return f"{collection_name}:{record_id}"


def split_redis_key(redis_key: str) -> tuple[str, str]:
    """Split a Redis key into its collection name and record ID.

    Args:
        redis_key (str): Redis key

    Returns:
        tuple[str, str]: Tuple of the collection name and ID
    """
    collection, record_id = redis_key.split(":")
    return collection, record_id


def serialize_record_to_redis(record: MemoryRecord, vector_type: np.dtype) -> dict[str, Any]:
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


def deserialize_redis_to_record(fields: dict[str, Any], vector_type: np.dtype, with_embedding: bool) -> MemoryRecord:
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
) -> MemoryRecord:
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


class RedisWrapper(Redis):
    def __del__(self) -> None:
        """Close connection, done when the object is deleted, used when SK creates a client."""
        self.close()


def data_model_definition_to_redis_fields(data_model_definition: VectorStoreRecordDefinition) -> list[RedisField]:
    """Create a list of fields for Redis from a data_model_definition."""
    fields: list[RedisField] = []
    for name, field in data_model_definition.fields.items():
        if isinstance(field, VectorStoreRecordVectorField):
            fields.append(
                VectorField(
                    name=name,
                    algorithm=field.index_kind.value.upper() if field.index_kind else "HNSW",
                    attributes={
                        "type": TYPE_MAPPER_VECTOR[field.property_type or "default"],
                        "dim": field.dimensions,
                        "distance_metric": DISTANCE_FUNCTION_MAP[field.distance_function or "default"],
                    },
                )
            )
            continue
        fields.append(TextField(name=name))
    return fields
