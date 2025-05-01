# Copyright (c) Microsoft. All rights reserved.
import json
from datetime import datetime
from typing import Any, cast
from unittest.mock import MagicMock

import numpy as np
from redis.commands.search.document import Document
from redis.commands.search.field import NumericField, TagField, TextField, VectorField

from semantic_kernel.connectors.memory.redis.const import (
    DISTANCE_FUNCTION_MAP,
    TYPE_MAPPER_VECTOR,
    RedisCollectionTypes,
)
from semantic_kernel.connectors.memory.redis.utils import (
    data_model_definition_to_redis_fields,
    deserialize_document_to_record,
    deserialize_redis_to_record,
    get_redis_key,
    serialize_record_to_redis,
    split_redis_key,
)
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.memory.memory_record import MemoryRecord


def test_get_and_split_redis_key_roundtrip() -> None:
    """Test that get_redis_key and split_redis_key compose and decompose keys correctly."""
    collection = "test_collection"
    record_id = "12345"
    key = get_redis_key(collection, record_id)
    assert key == f"{collection}:{record_id}"
    coll, rid = split_redis_key(key)
    assert coll == collection
    assert rid == record_id


def test_serialize_deserialize_local_record_without_embedding() -> None:
    """Test serialize and deserialize for local record without embedding retrieval."""
    embedding = np.array([0.1, 0.2, 0.3], dtype=float)
    record = MemoryRecord.local_record(
        id="id1",
        text="hello",
        description="desc",
        additional_metadata="meta",
        embedding=embedding,
        timestamp=None,
    )
    serialized = serialize_record_to_redis(record, vector_type=np.dtype(np.float32))
    assert serialized["key"] == ""
    assert serialized["timestamp"] == ""
    md = json.loads(serialized["metadata"])
    assert md["id"] == "id1"
    assert md["is_reference"] is False
    assert md["text"] == "hello"
    assert isinstance(serialized["embedding"], (bytes, bytearray))

    fields = {
        b"metadata": serialized["metadata"].encode(),
        b"timestamp": serialized["timestamp"].encode(),
        b"embedding": serialized["embedding"],
    }
    rec_no_embed = deserialize_redis_to_record(
        cast(dict[str, Any], fields),
        vector_type=np.dtype(np.float32),
        with_embedding=False,
    )
    assert rec_no_embed.id == "id1"
    assert rec_no_embed._embedding is None  # type: ignore
    assert rec_no_embed.timestamp is None


def test_serialize_deserialize_local_record_with_embedding_and_timestamp() -> None:
    """Test serialize and deserialize with embedding and timestamp included."""
    now = datetime.utcnow().replace(microsecond=0)
    embedding = np.array([1.0, 2.0, 3.0], dtype=float)
    record = MemoryRecord.local_record(
        id="id2",
        text="world",
        description=None,
        additional_metadata=None,
        embedding=embedding,
        timestamp=now,
    )
    serialized = serialize_record_to_redis(record, vector_type=np.dtype(np.float64))
    assert serialized["timestamp"] == now.isoformat()
    fields = {
        b"metadata": serialized["metadata"].encode(),
        b"timestamp": serialized["timestamp"].encode(),
        b"embedding": serialized["embedding"],
    }
    rec = deserialize_redis_to_record(
        cast(dict[str, Any], fields),
        vector_type=np.dtype(np.float64),
        with_embedding=True,
    )
    assert rec.id == "id2"
    assert rec.timestamp == now
    np.testing.assert_allclose(rec.embedding, embedding)  # type: ignore


def test_deserialize_document_to_record_without_and_with_embedding() -> None:
    """Test deserializing a Document-like mapping to a MemoryRecord with and without embedding."""
    fake_db = MagicMock()
    original_embedding = np.array([5.5, 6.5], dtype=np.float32)
    fake_db.hget.return_value = original_embedding.astype(np.float32).tobytes()

    timestamp = (datetime.utcnow().replace(microsecond=0)).isoformat()
    meta = {
        "id": "rid",
        "is_reference": True,
        "external_source_name": "src",
        "description": "d",
        "text": "t",
        "additional_metadata": "am",
    }
    # Prepare a mapping and cast to Document for typing
    doc_mapping = {
        "id": "col:rid",
        "metadata": json.dumps(meta),
        "timestamp": timestamp,
    }
    # Without embedding
    rec_no_embed = deserialize_document_to_record(
        fake_db,
        cast(Document, doc_mapping),
        vector_type=np.dtype(np.float32),
        with_embedding=False,
    )
    assert rec_no_embed.id == "rid"
    assert rec_no_embed._is_reference is True  # type: ignore
    assert rec_no_embed._external_source_name == "src"  # type: ignore
    assert rec_no_embed.timestamp == datetime.fromisoformat(timestamp)  # type: ignore
    assert rec_no_embed._embedding is None  # type: ignore

    # With embedding
    rec_with_embed = deserialize_document_to_record(
        fake_db,
        cast(Document, doc_mapping),
        vector_type=np.dtype(np.float32),
        with_embedding=True,
    )
    fake_db.hget.assert_called_with("col:rid", "embedding")
    np.testing.assert_allclose(rec_with_embed.embedding, original_embedding.astype(float))  # type: ignore


def test_data_model_definition_to_redis_fields_hashset_and_json() -> None:
    """Test that data_model_definition_to_redis_fields converts definition correctly for both HASHSET and JSON."""
    fields = {
        "key": VectorStoreRecordKeyField(name="key"),
        "vec": VectorStoreRecordVectorField(name="vec", dimensions=3),
        "num": VectorStoreRecordDataField(name="num", property_type="int"),
        "txt": VectorStoreRecordDataField(name="txt", property_type="str", is_full_text_searchable=True),
        "tag": VectorStoreRecordDataField(name="tag", property_type="str", is_full_text_searchable=False),
    }
    definition = VectorStoreRecordDefinition(fields=fields)
    hash_fields = data_model_definition_to_redis_fields(definition, RedisCollectionTypes.HASHSET)
    names = {f.name for f in hash_fields}
    assert names == {"vec", "num", "txt", "tag"}
    for f in hash_fields:
        if f.name == "vec":
            assert isinstance(f, VectorField)
            args = getattr(f, "args")
            assert args[1] == "HNSW"
            assert args[4] == TYPE_MAPPER_VECTOR["default"]
            assert args[6] == 3
            assert args[8] == DISTANCE_FUNCTION_MAP["default"]
        elif f.name == "num":
            assert isinstance(f, NumericField)
        elif f.name == "txt":
            assert isinstance(f, TextField)
        elif f.name == "tag":
            assert isinstance(f, TagField)

    json_fields = data_model_definition_to_redis_fields(definition, RedisCollectionTypes.JSON)
    json_names = {f.name for f in json_fields}
    assert json_names == {"$.vec", "$.num", "$.txt", "$.tag"}
    for f in json_fields:
        if isinstance(f, VectorField):
            assert f.as_name == "vec"
        else:
            assert getattr(f, "as_name") in {"num", "txt", "tag"}
