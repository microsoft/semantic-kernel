# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict
from semantic_kernel.memory.memory_record import MemoryRecord

def build_payload(record: MemoryRecord) -> dict:
    """
    Builds a metadata payload to be sent to Pinecone from a MemoryRecord.
    """
    payload: dict = {}
    payload["_id"] = record._id
    payload["$vector"]= record.embedding.tolist()
    if record._text:
        payload["text"] = record._text
    if record._description:
        payload["description"] = record._description
    if record._additional_metadata:
        payload["additional_metadata"] = record._additional_metadata
    return payload


def parse_payload(record: Dict) -> MemoryRecord:
    """
    Parses a record from Pinecone into a MemoryRecord.
    """
    text = record["text"]
    description = record["description"]
    additional_metadata = record["additional_metadata"]

    return MemoryRecord.local_record(
        id=record._id,
        description=description,
        text=text,
        additional_metadata=additional_metadata,
        embedding=record["$vector"],
    )
