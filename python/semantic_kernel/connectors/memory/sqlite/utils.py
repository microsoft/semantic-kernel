import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord


@dataclass
class Metadata:
    # Whether the source data used to calculate embeddings are stored in the local
    # storage provider or is available through and external service, such as web site, MS Graph, etc.
    is_reference: bool

    # A value used to understand which external service owns the data, to avoid storing the information
    # inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
    external_source_name: str

    # Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
    id: str

    # Optional title describing the content. Note: the title is not indexed.
    description: str

    # Source text, available only when the memory is not an external source.
    text: str

    # Field for saving custom metadata with a memory.
    additional_metadata: str

    @staticmethod
    def from_memory_record(record: MemoryRecord) -> "Metadata":
        return Metadata(
            is_reference=record._is_reference,
            external_source_name=record._external_source_name,
            id=record._id or record._key,
            description=record._description,
            text=record._text,
            additional_metadata=record._additional_metadata,
        )

    def to_json(self) -> str:
        return serialize_metadata(self)

    @staticmethod
    def from_json(json: str) -> "Metadata":
        d = deserialize_metadata(json)
        return Metadata(
            is_reference=d["is_reference"] or False,
            external_source_name=d["external_source_name"] or "",
            id=d["id"] or "",
            description=d["description"] or "",
            text=d["text"] or "",
            additional_metadata=d["additional_metadata"] or "",
        )


def serialize_metadata(metadata: Metadata) -> str:
    return json.dumps(asdict(metadata))


def deserialize_metadata(metadata: str) -> defaultdict:
    return defaultdict(lambda: None, json.loads(metadata))


def deserialize_embedding(embedding: str) -> np.ndarray:
    return np.array(json.loads(embedding), dtype=np.float32)


def serialize_embedding(embedding: np.ndarray) -> str:
    return json.dumps(embedding.tolist())


# C# implementation uses `timestamp?.ToString("u", CultureInfo.InvariantCulture);` to serialize timestamps.
# which is the below format according to https://stackoverflow.com/questions/46778141/datetime-formats-used-in-invariantculture
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%fZ"


def deserialize_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT) if timestamp else None


def serialize_timestamp(timestamp: Optional[datetime]) -> Optional[str]:
    return timestamp.strftime(TIMESTAMP_FORMAT) if timestamp else None
