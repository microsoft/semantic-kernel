# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock

import numpy as np
from pytest import CaptureFixture

from samples.concepts.local_models.lm_studio_text_embedding import (
    MemoryRecord,
    populate_memory,
    search_memory_examples,
)
from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.in_memory import InMemoryCollection


async def test_lm_studio_embedding_sample_uses_vector_collection(capsys: CaptureFixture[str]) -> None:
    contents = [
        "Your budget for 2024 is $100,000",
        "Your savings from 2023 are $50,000",
        "Your investments are $80,000",
    ]
    questions = [
        "What is my budget for 2024?",
        "What are my savings from 2023?",
        "What are my investments?",
    ]
    vectors = np.eye(3, 768)
    embeddings = dict(zip(contents + questions, list(vectors) + list(vectors)))

    async def generate_embeddings(texts: list[str], **kwargs) -> np.ndarray:
        return np.array([embeddings[text] for text in texts])

    embedding_generator = AsyncMock(spec=EmbeddingGeneratorBase)
    embedding_generator.generate_embeddings.side_effect = generate_embeddings
    embedding_generator.generate_raw_embeddings.side_effect = generate_embeddings

    async with InMemoryCollection[str, MemoryRecord](
        record_type=MemoryRecord,
        embedding_generator=embedding_generator,
    ) as collection:
        await collection.ensure_collection_exists()
        await populate_memory(collection)
        await search_memory_examples(collection)

    output = capsys.readouterr().out
    for content in contents:
        assert f"Answer: {content}" in output
