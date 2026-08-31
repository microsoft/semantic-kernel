# Copyright (c) Microsoft. All rights reserved.

import importlib
import sys
from unittest.mock import patch

import pytest

import semantic_kernel.connectors.memory as memory_module
import semantic_kernel.connectors.search as search_module
from semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings import (
    HuggingFacePromptExecutionSettings,
)
from semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base import (
    OnnxGenAICompletionBase,
)
from semantic_kernel.connectors.memory_stores.chroma.chroma_memory_store import (
    ChromaMemoryStore,
)
from semantic_kernel.exceptions import ServiceInitializationError


@pytest.mark.parametrize(
    "symbol_name,expected_extra",
    [
        ("AzureAISearchCollection", "azure"),
        ("AzureAISearchSettings", "azure"),
        ("AzureAISearchStore", "azure"),
        ("CosmosNoSqlCollection", "azure"),
        ("CosmosNoSqlCompositeKey", "azure"),
        ("CosmosNoSqlSettings", "azure"),
        ("CosmosNoSqlStore", "azure"),
        ("CosmosMongoCollection", "azure"),
        ("CosmosMongoSettings", "azure"),
        ("CosmosMongoStore", "azure"),
        ("ChromaCollection", "chroma"),
        ("ChromaStore", "chroma"),
        ("PostgresCollection", "postgres"),
        ("PostgresSettings", "postgres"),
        ("PostgresStore", "postgres"),
        ("FaissCollection", "faiss"),
        ("FaissStore", "faiss"),
        ("MongoDBAtlasCollection", "mongo"),
        ("MongoDBAtlasSettings", "mongo"),
        ("MongoDBAtlasStore", "mongo"),
        ("OracleCollection", "oracledb"),
        ("OracleSettings", "oracledb"),
        ("OracleStore", "oracledb"),
        ("RedisStore", "redis"),
        ("RedisSettings", "redis"),
        ("RedisCollectionTypes", "redis"),
        ("RedisHashsetCollection", "redis"),
        ("RedisJsonCollection", "redis"),
        ("QdrantCollection", "qdrant"),
        ("QdrantSettings", "qdrant"),
        ("QdrantStore", "qdrant"),
        ("WeaviateCollection", "weaviate"),
        ("WeaviateSettings", "weaviate"),
        ("WeaviateStore", "weaviate"),
        ("PineconeCollection", "pinecone"),
        ("PineconeSettings", "pinecone"),
        ("PineconeStore", "pinecone"),
        ("SqlServerCollection", "sql"),
        ("SqlServerStore", "sql"),
        ("SqlSettings", "sql"),
    ],
)
def test_memory_lazy_import_missing_dependency(symbol_name: str, expected_extra: str):
    """Test that importing a connector raises ModuleNotFoundError with the exact install extra."""
    submod_name = memory_module._IMPORTS[symbol_name]

    def mock_import_module(name: str, package: str | None = None):
        if name == submod_name:
            raise ModuleNotFoundError(f"No module named 'fake_{expected_extra}'", name=f"fake_{expected_extra}")
        return importlib.__import__(name)

    with (
        patch("importlib.import_module", side_effect=mock_import_module),
        pytest.raises(ModuleNotFoundError) as exc_info,
    ):
        getattr(memory_module, symbol_name)

    assert f"pip install semantic-kernel[{expected_extra}]" in str(exc_info.value)
    assert symbol_name in str(exc_info.value)


def test_memory_in_memory_import():
    """Test that built-in InMemory store and collection import successfully without extra dependencies."""
    in_memory_col = getattr(memory_module, "InMemoryCollection")
    assert in_memory_col is not None

    in_memory_store = getattr(memory_module, "InMemoryStore")
    assert in_memory_store is not None


def test_memory_unknown_attribute():
    """Test that accessing an unknown attribute in memory module raises AttributeError."""
    with pytest.raises(
        AttributeError,
        match="module semantic_kernel.connectors.memory has no attribute NonExistentStore",
    ):
        getattr(memory_module, "NonExistentStore")


def test_memory_dir():
    """Test that __dir__ lists all available memory symbols."""
    dir_symbols = dir(memory_module)
    for symbol in [
        "ChromaCollection",
        "QdrantCollection",
        "WeaviateCollection",
        "PineconeCollection",
        "PostgresCollection",
        "RedisStore",
        "MongoDBAtlasCollection",
        "FaissCollection",
        "OracleCollection",
        "SqlServerCollection",
        "AzureAISearchCollection",
        "CosmosNoSqlCollection",
        "InMemoryCollection",
    ]:
        assert symbol in dir_symbols


def test_search_imports():
    """Test that search connectors can be imported and non-existent attribute raises AttributeError."""
    google_search = getattr(search_module, "GoogleSearch")
    assert google_search is not None

    brave_search = getattr(search_module, "BraveSearch")
    assert brave_search is not None

    with pytest.raises(AttributeError, match="has no attribute NonExistentSearch"):
        getattr(search_module, "NonExistentSearch")


def test_chroma_memory_store_missing_dependency():
    """Test that ChromaMemoryStore raises ServiceInitializationError when chromadb is missing."""
    with (
        patch.dict(sys.modules, {"chromadb": None, "chromadb.config": None}),
        pytest.raises(ServiceInitializationError, match=r"pip install semantic-kernel\[chroma\]"),
    ):
        ChromaMemoryStore()


def test_onnx_gen_ai_completion_missing_dependency():
    """Test that OnnxGenAICompletionBase raises ServiceInitializationError when onnxruntime-genai is missing."""
    with (
        patch("semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base.ready", False),
        pytest.raises(ServiceInitializationError, match=r"pip install semantic-kernel\[onnx\]"),
    ):
        OnnxGenAICompletionBase(ai_model_path="fake_path")


def test_hugging_face_settings_missing_dependency():
    """Test that HuggingFacePromptExecutionSettings raises ServiceInitializationError when transformers is missing."""
    with (
        patch("semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings.ready", False),
        pytest.raises(ServiceInitializationError, match=r"pip install semantic-kernel\[hugging_face\]"),
    ):
        settings = HuggingFacePromptExecutionSettings()
        settings.get_generation_config()
