# Copyright (c) Microsoft. All rights reserved.

from typing import Optional
from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from semantic_kernel.kernel_pydantic import HttpsUrl

class BaseModelSettings(BaseSettings):
    """Base model settings with shared configuration."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class PostgresSettings(BaseModelSettings):
    """Postgres model settings

    Required:
    - connection_string: str - Postgres connection string
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "POSTGRES_"})
    connection_string: str | PostgresDsn


class PineconeSettings(BaseModelSettings):
    """Pinecone model settings

    Required:
    - api_key: SecretStr - Pinecone API key
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "PINECONE_"})
    api_key: SecretStr


class AstraDBSettings(BaseModelSettings):
    """AstraDB model settings

    Required:
    - app_token: SecretStr - AstraDB token
    - db_id: str - AstraDB database ID
    - region: str - AstraDB region
    - keyspace: str - AstraDB keyspace
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "ASTRADB_"})
    app_token: SecretStr
    db_id: str
    region: str
    keyspace: str


class WeaviateSettings(BaseModelSettings):
    """Weaviate model settings

    Required:
    - url: HttpUrl - Weaviate URL
    - api_key: SecretStr - Weaviate token
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "WEAVIATE_"})
    url: HttpsUrl = Field(..., description="Weaviate URL")
    api_key: SecretStr = Field(..., description="Weaviate token")


class MongoDBAtlasSettings(BaseModelSettings):
    """MongoDB Atlas model settings

    Required:
    - connection_string: str - MongoDB Atlas connection string
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "MONGODB_"})
    connection_string: str


class AzureCosmosDBSettings(BaseModelSettings):
    """Azure CosmosDB model settings

    Required:
    - connection_string: str - Azure CosmosDB connection string
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "COSMOSDB_"})
    api: str
    connection_string: str


class RedisSettings(BaseModelSettings):
    """Redis model settings

    Required:
    - connection_string: str - Redis connection string
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "REDIS_"})
    connection_string: str


class AzureAISearchSettings(BaseModelSettings):
    """Azure AI Search model settings

    Required:
    - api_key: SecretStr - Azure AI Search API key
    - endpoint: HttpsUrl - Azure AI Search endpoint
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "AZURE_AI_SEARCH_"})
    api_key: SecretStr
    endpoint: HttpsUrl
    index_name: str


class AzureKeyVaultSettings(BaseModelSettings):
    """Azure Key Vault model settings

    Required:
    - vault_url: HttpsUrl - Azure Key Vault URL
    - client_id: str - Azure Key Vault client ID
    - client_secret: SecretStr - Azure Key Vault client secret
    """
    model_config = BaseModelSettings.model_config.copy(update={"env_prefix": "AZURE_KEYVAULT_"})
    endpoint: HttpsUrl
    client_id: str
    client_secret: SecretStr


