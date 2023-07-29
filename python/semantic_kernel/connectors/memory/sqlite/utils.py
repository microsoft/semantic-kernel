import json
import numpy as np
from datetime import datetime


def deserialize_metadata(metadata: str) -> dict:
    return json.loads(metadata)


def deserialize_embedding(embedding: str) -> np.ndarray:
    return np.array(json.loads(embedding), dtype=np.float32)


def serialize_embedding(embedding: np.ndarray) -> str:
    return json.dumps(embedding.tolist())


def deserialize_timestamp(timestamp: str) -> datetime:
    # note: this is not the correct format
    return datetime.strptime(timestamp, "yyyy-MM-dd HH:mm:ssZ")


def serialize_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime("yyyy-MM-dd HH:mm:ssZ")
