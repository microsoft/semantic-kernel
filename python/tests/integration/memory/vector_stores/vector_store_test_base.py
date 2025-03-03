# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

import pytest

from semantic_kernel.data import VectorStore


def get_redis_store():
    from semantic_kernel.connectors.memory.redis.redis_store import RedisStore

    return RedisStore()


def get_azure_ai_search_store():
    from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_store import AzureAISearchStore

    return AzureAISearchStore()


def get_qdrant_store():
    from semantic_kernel.connectors.memory.qdrant.qdrant_store import QdrantStore

    return QdrantStore()


def get_qdrant_store_in_memory():
    from semantic_kernel.connectors.memory.qdrant.qdrant_store import QdrantStore

    return QdrantStore(location=":memory:")


def get_weaviate_store():
    from semantic_kernel.connectors.memory.weaviate.weaviate_store import WeaviateStore

    return WeaviateStore(local_host="localhost")


def get_azure_cosmos_db_no_sql_store():
    from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_store import (
        AzureCosmosDBNoSQLStore,
    )

    return AzureCosmosDBNoSQLStore(database_name="test_database", create_database=True)


def get_chroma_store():
    from semantic_kernel.connectors.memory.chroma.chroma import ChromaStore

    return ChromaStore()


class VectorStoreTestBase:
    @pytest.fixture
    def stores(self) -> dict[str, Callable[[], VectorStore]]:
        """Return a dictionary of vector stores to test."""
        return {
            "redis": get_redis_store,
            "azure_ai_search": get_azure_ai_search_store,
            "qdrant": get_qdrant_store,
            "qdrant_in_memory": get_qdrant_store_in_memory,
            "weaviate_local": get_weaviate_store,
            "azure_cosmos_db_no_sql": get_azure_cosmos_db_no_sql_store,
            "chroma": get_chroma_store,
        }
