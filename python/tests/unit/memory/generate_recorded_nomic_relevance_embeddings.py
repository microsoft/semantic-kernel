# Copyright (c) Microsoft. All rights reserved.
"""Regenerate the offline relevance fixture from a local LM Studio server."""

import json
import struct
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

MODEL = "text-embedding-nomic-embed-text-v1.5"
CHECKPOINT = "nomic-ai/nomic-embed-text-v1.5"
ENDPOINT = "http://127.0.0.1:1234/v1/embeddings"
TEXTS = {
    "stored": "Before deleting user data, require explicit confirmation.",
    "negated_query": "Before deleting user data, do not require explicit confirmation.",
    "paraphrase_stored": "Erase records only after the subject has authorized the action.",
    "paraphrase_query": "Obtain affirmative consent from the person before erasing any of their personal information.",
}
OUTPUT = Path(__file__).with_name("recorded_nomic_relevance_embeddings.json")


def embed(text: str) -> list[float]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"model": MODEL, "input": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)["data"][0]["embedding"]


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    return dot / (left_norm * right_norm)


vectors = {name: embed(text) for name, text in TEXTS.items()}
OUTPUT.write_text(
    json.dumps(
        {
            "model": MODEL,
            "checkpoint": CHECKPOINT,
            "endpoint": ENDPOINT,
            "generator": "python tests/unit/memory/generate_recorded_nomic_relevance_embeddings.py",
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "dimension": len(vectors["stored"]),
            "float_format": "IEEE-754 float32",
            "texts": TEXTS,
            "cosine_similarity": {
                "stored_to_negated_query": cosine(vectors["stored"], vectors["negated_query"]),
                "paraphrase_stored_to_query": cosine(vectors["paraphrase_stored"], vectors["paraphrase_query"]),
            },
            "vectors": {
                name: list(struct.unpack(f"<{len(vector)}f", struct.pack(f"<{len(vector)}f", *vector)))
                for name, vector in vectors.items()
            },
        },
        indent=2,
    )
    + "\n"
)
