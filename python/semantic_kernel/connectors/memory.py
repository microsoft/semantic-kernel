# Copyright (c) Microsoft. All rights reserved.

import importlib
from typing import Any

_IMPORTS: dict[str, str] = {
    "AzureAISearchCollection": ".azure_ai_search",
    "AzureAISearchSettings": ".azure_ai_search",
    "AzureAISearchStore": ".azure_ai_search",
    "CosmosNoSqlCollection": ".azure_cosmos_db",
    "CosmosNoSqlCompositeKey": ".azure_cosmos_db",
    "CosmosNoSqlSettings": ".azure_cosmos_db",
    "CosmosNoSqlStore": ".azure_cosmos_db",
    "CosmosMongoCollection": ".azure_cosmos_db",
    "CosmosMongoSettings": ".azure_cosmos_db",
    "CosmosMongoStore": ".azure_cosmos_db",
    "ChromaCollection": ".chroma",
    "ChromaStore": ".chroma",
    "PostgresCollection": ".postgres",
    "PostgresSettings": ".postgres",
    "PostgresStore": ".postgres",
    "FaissCollection": ".faiss",
    "FaissStore": ".faiss",
    "InMemoryCollection": ".in_memory",
    "InMemoryStore": ".in_memory",
    "MongoDBAtlasCollection": ".mongodb",
    "MongoDBAtlasSettings": ".mongodb",
    "MongoDBAtlasStore": ".mongodb",
    "OracleCollection": ".oracle",
    "OracleSettings": ".oracle",
    "OracleStore": ".oracle",
    "RedisStore": ".redis",
    "RedisSettings": ".redis",
    "RedisCollectionTypes": ".redis",
    "RedisHashsetCollection": ".redis",
    "RedisJsonCollection": ".redis",
    "QdrantCollection": ".qdrant",
    "QdrantSettings": ".qdrant",
    "QdrantStore": ".qdrant",
    "WeaviateCollection": ".weaviate",
    "WeaviateSettings": ".weaviate",
    "WeaviateStore": ".weaviate",
    "PineconeCollection": ".pinecone",
    "PineconeSettings": ".pinecone",
    "PineconeStore": ".pinecone",
    "SqlServerCollection": ".sql_server",
    "SqlServerStore": ".sql_server",
    "SqlSettings": ".sql_server",
}

_EXTRA_MAP: dict[str, str] = {
    ".azure_ai_search": "azure",
    ".azure_cosmos_db": "azure",
    ".chroma": "chroma",
    ".faiss": "faiss",
    ".mongodb": "mongo",
    ".oracle": "oracledb",
    ".pinecone": "pinecone",
    ".postgres": "postgres",
    ".qdrant": "qdrant",
    ".redis": "redis",
    ".sql_server": "sql",
    ".weaviate": "weaviate",
}


def __getattr__(name: str) -> Any:
    if name in _IMPORTS:
        submod_name = _IMPORTS[name]
        try:
            module = importlib.import_module(submod_name, package=__package__)
            return getattr(module, name)
        except (ModuleNotFoundError, ImportError) as ex:
            extra = _EXTRA_MAP.get(submod_name)
            if extra:
                raise ModuleNotFoundError(
                    f"Could not import {name} from {submod_name}. "
                    f"Please install the optional dependency with `pip install semantic-kernel[{extra}]`."
                ) from ex
            raise
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__() -> list[str]:
    return list(_IMPORTS.keys())
