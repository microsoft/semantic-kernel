# Copyright (c) Microsoft. All rights reserved.
from typing import Any, Dict

import aiohttp
import numpy

from semantic_kernel.memory.memory_record import MemoryRecord


class AsyncSession:
    def __init__(self, session: aiohttp.ClientSession = None):
        self._session = session if session else aiohttp.ClientSession()

    async def __aenter__(self):
        return await self._session.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        await self._session.close()


def build_payload(record: MemoryRecord) -> Dict[str, Any]:
    """
    Builds a metadata payload to be sent to AstraDb from a MemoryRecord.
    """
    payload: Dict[str, Any] = {}
    payload["$vector"] = record.embedding.tolist()
    if record._text:
        payload["text"] = record._text
    if record._description:
        payload["description"] = record._description
    if record._additional_metadata:
        payload["additional_metadata"] = record._additional_metadata
    return payload


def parse_payload(document: Dict[str, Any]) -> MemoryRecord:
    """
    Parses a record from AstraDb into a MemoryRecord.
    """
    text = document.get("text", None)
    description = document["description"] if "description" in document else None
    additional_metadata = document["additional_metadata"] if "additional_metadata" in document else None

    return MemoryRecord.local_record(
        id=document["_id"],
        description=description,
        text=text,
        additional_metadata=additional_metadata,
        embedding=document["$vector"] if "$vector" in document else numpy.array([]),
    )
