import json
import numpy as np
from datetime import datetime


def deserialize_metadata(metadata: str) -> dict:
    return json.loads(metadata)


def deserialize_embedding(embedding: str) -> np.ndarray:
    return np.array(json.loads(embedding), dtype=np.float32)


def serialize_embedding(embedding: np.ndarray) -> str:
    return json.dumps(embedding.tolist())


# C# implementation uses `timestamp?.ToString("u", CultureInfo.InvariantCulture);` to serialize timestamps.
# which is the below format accoridng to https://stackoverflow.com/questions/46778141/datetime-formats-used-in-invariantculture
TIMESTAMP_FORMAT = "yyyy-MM-dd HH:mm:ssZ"


def deserialize_timestamp(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT)


def serialize_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime(TIMESTAMP_FORMAT)
