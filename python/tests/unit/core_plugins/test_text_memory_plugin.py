# Copyright (c) Microsoft. All rights reserved.


from numpy import array
from pytest import fixture

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


class MockEmbeddings(EmbeddingGeneratorBase):
    async def generate_embeddings(self, texts, **kwargs):
        dims = 10
        return array([[idx for idx in range(dims)]])


@fixture
def memory() -> SemanticTextMemory:
    store = VolatileMemoryStore()
    return SemanticTextMemory(store, MockEmbeddings(service_id="embed", ai_model_id="mock"))


@fixture
async def memory_with_records(memory: SemanticTextMemory) -> SemanticTextMemory:
    await memory.save_information("generic", "hello world", "1")
    return memory


def test_can_be_instantiated(memory: SemanticTextMemory):
    assert TextMemoryPlugin(memory)


def test_can_be_imported(kernel: Kernel, memory: SemanticTextMemory):
    kernel.add_plugin(TextMemoryPlugin(memory), "memory_plugin")
    assert not kernel.get_function(plugin_name="memory_plugin", function_name="recall").is_prompt


async def test_can_save(memory: SemanticTextMemory):
    text_plugin = TextMemoryPlugin(memory)
    await text_plugin.save(text="hello you", key="1")
    assert text_plugin.memory._storage._store["generic"]["1"].text == "hello you"


async def test_can_recall(memory_with_records: SemanticTextMemory):
    text_plugin = TextMemoryPlugin(memory_with_records)
    result = await text_plugin.recall(ask="hello world")
    assert result == "hello world"


async def test_can_save_through_function(kernel: Kernel, memory: SemanticTextMemory):
    text_plugin = TextMemoryPlugin(memory)
    kernel.add_plugin(text_plugin, "memory_plugin")
    await kernel.invoke(function_name="save", plugin_name="memory_plugin", text="hello world", key="1")
    assert text_plugin.memory._storage._store["generic"]["1"].text == "hello world"


async def test_can_recall_through_function(kernel: Kernel, memory_with_records: SemanticTextMemory):
    text_plugin = TextMemoryPlugin(memory_with_records)
    kernel.add_plugin(text_plugin, "memory_plugin")
    result = await kernel.invoke(function_name="recall", plugin_name="memory_plugin", ask="hello world")
    assert str(result) == "hello world"


async def test_can_recall_no_result(memory: SemanticTextMemory):
    text_plugin = TextMemoryPlugin(memory)
    result = await text_plugin.recall(ask="hello world")
    assert result == ""
