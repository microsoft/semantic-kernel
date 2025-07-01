# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

import pytest

from semantic_kernel.data.vector import VectorStore


def get_redis_store():
    from semantic_kernel.connectors.redis import RedisStore

    return RedisStore()


def get_azure_ai_search_store():
    from semantic_kernel.connectors.azure_ai_search import AzureAISearchStore

    return AzureAISearchStore()


def get_qdrant_store():
    from semantic_kernel.connectors.qdrant import QdrantStore

    return QdrantStore()


def get_qdrant_store_in_memory():
    from semantic_kernel.connectors.qdrant import QdrantStore

    return QdrantStore(location=":memory:")


def get_weaviate_store():
    from semantic_kernel.connectors.weaviate import WeaviateStore

    return WeaviateStore(local_host="localhost")


def get_azure_cosmos_db_no_sql_store():
    from semantic_kernel.connectors.azure_cosmos_db import CosmosNoSqlStore

    return CosmosNoSqlStore(database_name="test_database", create_database=True)


def get_chroma_store():
    from semantic_kernel.connectors.chroma import ChromaStore

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
