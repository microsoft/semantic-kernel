# Copyright (c) Microsoft. All rights reserved.
import numpy
from typing import Dict
from semantic_kernel.memory.memory_record import MemoryRecord


def build_payload(record: MemoryRecord) -> dict:
    """
    Builds a metadata payload to be sent to Pinecone from a MemoryRecord.
    """
    payload: dict = {}
    payload["_id"] = record._id
    payload["$vector"] = record.embedding.tolist()
    if record._text:
        payload["text"] = record._text
    if record._description:
        payload["description"] = record._description
    if record._additional_metadata:
        payload["additional_metadata"] = record._additional_metadata
    return payload


def parse_payload(document: Dict) -> MemoryRecord:
    """
    Parses a record from Pinecone into a MemoryRecord.
    """
    text = document["text"] if "text" in document else None
    description = document["description"] if "description" in document else None
    additional_metadata = document["additional_metadata"] if "additional_metadata" in document else None

    return MemoryRecord.local_record(
        id=document._id,
        description=description,
        text=text,
        additional_metadata=additional_metadata,
        embedding=document["vector"] if "$vector" in document else numpy.array([
        ]),
    )
