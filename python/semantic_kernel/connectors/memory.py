# Copyright (c) Microsoft. All rights reserved.

import importlib

_IMPORTS = {
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


def __getattr__(name: str):
    if name in _IMPORTS:
        submod_name = _IMPORTS[name]
        module = importlib.import_module(submod_name, package=__name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__():
    return list(_IMPORTS.keys())
