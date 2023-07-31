import json
import numpy as np
from datetime import datetime
from typing import Optional
from semantic_kernel.memory.memory_record import MemoryRecord

from dataclasses import dataclass, asdict


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

    # Field for saving custom metadata with a memory.
    additional_metadata: str

    @staticmethod
    def from_memory_record(record: MemoryRecord) -> "Metadata":
        return Metadata(
            record._is_reference,
            record._external_source_name,
            record._id,
            record._description,
            record._additional_metadata,
        )

    def to_json(self) -> str:
        return serialize_metadata(self)

    @staticmethod
    def from_json(json: str) -> "Metadata":
        d = deserialize_metadata(json)
        return Metadata(
            d["is_reference"],
            d["external_source_name"],
            d["id"],
            d["description"],
            d["additional_metadata"],
        )


def serialize_metadata(metadata: Metadata) -> str:
    return json.dumps(asdict(metadata))


def deserialize_metadata(metadata: str) -> dict:
    return json.loads(metadata)


def deserialize_embedding(embedding: str) -> np.ndarray:
    return np.array(json.loads(embedding), dtype=np.float32)


def serialize_embedding(embedding: np.ndarray) -> str:
    return json.dumps(embedding.tolist())


# C# implementation uses `timestamp?.ToString("u", CultureInfo.InvariantCulture);` to serialize timestamps.
# which is the below format accoridng to https://stackoverflow.com/questions/46778141/datetime-formats-used-in-invariantculture
TIMESTAMP_FORMAT = "yyyy-MM-dd HH:mm:ssZ"


def deserialize_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT) if timestamp else None


def serialize_timestamp(timestamp: Optional[datetime]) -> Optional[str]:
    return timestamp.strftime(TIMESTAMP_FORMAT) if timestamp else None
