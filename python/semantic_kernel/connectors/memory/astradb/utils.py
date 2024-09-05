# Copyright (c) Microsoft. All rights reserved.
from typing import Any

import aiohttp
import numpy

from semantic_kernel.memory.memory_record import MemoryRecord


class AsyncSession:
    """A wrapper around aiohttp.ClientSession that can be used as an async context manager."""

    def __init__(self, session: aiohttp.ClientSession = None):
        """Initializes a new instance of the AsyncSession class."""
        self._session = session if session else aiohttp.ClientSession()

    async def __aenter__(self):
        """Enter the session."""
        return await self._session.__aenter__()

    async def __aexit__(self, *args, **kwargs):
        """Close the session."""
        await self._session.close()


def build_payload(record: MemoryRecord) -> dict[str, Any]:
    """Builds a metadata payload to be sent to AstraDb from a MemoryRecord."""
    payload: dict[str, Any] = {}
    payload["$vector"] = record.embedding.tolist()
    if record._text:
        payload["text"] = record._text
    if record._description:
        payload["description"] = record._description
    if record._additional_metadata:
        payload["additional_metadata"] = record._additional_metadata
    return payload


def parse_payload(document: dict[str, Any]) -> MemoryRecord:
    """Parses a record from AstraDb into a MemoryRecord."""
    text = document.get("text")
    description = document.get("description")
    additional_metadata = document.get("additional_metadata")

    return MemoryRecord.local_record(
        id=document["_id"],
        description=description,
        text=text,
        additional_metadata=additional_metadata,
        embedding=document["$vector"] if "$vector" in document else numpy.array([]),
    )
