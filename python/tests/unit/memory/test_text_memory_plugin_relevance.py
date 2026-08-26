# Copyright (c) Microsoft. All rights reserved.

import numpy as np

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore
from tests.unit.memory.recorded_nomic_relevance_embeddings import RECORDED_EMBEDDINGS

STORED_TEXT = "Before deleting user data, require explicit confirmation."
NEGATED_QUERY = "Before deleting user data, do not require explicit confirmation."
PARAPHRASE_STORED_TEXT = "Erase records only after the subject has authorized the action."
PARAPHRASE_QUERY = "Obtain affirmative consent from the person before erasing any of their personal information."


class RecordedEmbeddingGenerator(EmbeddingGeneratorBase):
    async def generate_embeddings(self, texts, settings=None, **kwargs):
        return np.array([RECORDED_EMBEDDINGS[text] for text in texts], dtype=np.float32)


async def test_recall_default_threshold_returns_negated_instruction():
    memory = SemanticTextMemory(VolatileMemoryStore(), RecordedEmbeddingGenerator(ai_model_id="recorded-nomic"))
    plugin = TextMemoryPlugin(memory)

    await plugin.save(STORED_TEXT, "stored")

    result = await plugin.recall(NEGATED_QUERY)

    assert result == STORED_TEXT


async def test_recall_default_threshold_filters_equivalent_paraphrase():
    memory = SemanticTextMemory(VolatileMemoryStore(), RecordedEmbeddingGenerator(ai_model_id="recorded-nomic"))
    plugin = TextMemoryPlugin(memory)

    await plugin.save(PARAPHRASE_STORED_TEXT, "stored")

    result = await plugin.recall(PARAPHRASE_QUERY)

    assert result == ""


def test_recorded_vectors_cross_the_default_relevance_threshold():
    stored = np.array(RECORDED_EMBEDDINGS[STORED_TEXT])
    negated = np.array(RECORDED_EMBEDDINGS[NEGATED_QUERY])
    paraphrase_stored = np.array(RECORDED_EMBEDDINGS[PARAPHRASE_STORED_TEXT])
    paraphrase_query = np.array(RECORDED_EMBEDDINGS[PARAPHRASE_QUERY])

    assert np.dot(stored, negated) / (np.linalg.norm(stored) * np.linalg.norm(negated)) > 0.75
    assert np.dot(paraphrase_stored, paraphrase_query) / (
        np.linalg.norm(paraphrase_stored) * np.linalg.norm(paraphrase_query)
    ) < 0.75
