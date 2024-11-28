# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_store import AzureAISearchStore
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_store import AzureCosmosDBNoSQLStore
from semantic_kernel.connectors.memory.qdrant.qdrant_store import QdrantStore
from semantic_kernel.connectors.memory.redis.redis_store import RedisStore
from semantic_kernel.connectors.memory.weaviate.weaviate_store import WeaviateStore
from semantic_kernel.data import VectorStore


class VectorStoreTestBase:
    @pytest.fixture
    def stores(self) -> dict[str, VectorStore]:
        """Return a dictionary of vector stores to test."""
        return {
            "redis": RedisStore(),
            "azure_ai_search": AzureAISearchStore(),
            "qdrant": QdrantStore(),
            "qdrant_in_memory": QdrantStore(location=":memory:"),
            "weaviate_local": WeaviateStore(local_host="localhost"),
            "azure_cosmos_db_no_sql": AzureCosmosDBNoSQLStore(database_name="test_database", create_database=True),
        }
