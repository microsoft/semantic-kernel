# Copyright (c) Microsoft. All rights reserved.

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings

from semantic_kernel.kernel_pydantic import HttpsUrl


class BaseModelSettings(BaseSettings):
    use_env_settings_file: bool = False

    class Config:
        env_file = None
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False

    @classmethod
    def create(cls, **kwargs):
        if kwargs.pop("use_env_settings_file", False):
            cls.Config.env_file = ".env"
        return cls(**kwargs)


class AzureAISearchSettings(BaseModelSettings):
    """Azure AI Search model settings currently used by the AzureCognitiveSearchMemoryStore connector

    Required:
    - api_key: SecretStr - Azure AI Search API key (Env var AZURE_AI_SEARCH_API_KEY)
    - endpoint: HttpsUrl - Azure AI Search endpoint (Env var AZURE_AI_SEARCH_ENDPOINT)
    - index_name: str - Azure AI Search index name (Env var AZURE_AI_SEARCH_INDEX_NAME)
    """

    api_key: SecretStr
    endpoint: HttpsUrl
    index_name: str

    class Config(BaseModelSettings.Config):
        env_prefix = "AZURE_AI_SEARCH_"

    def model_dump(self):
        """
        Custom method to dump model data in the required format.
        """
        return {
            "api_key": self.api_key.get_secret_value(),
            "endpoint": str(self.endpoint),
            "index_name": self.index_name,
        }


class AzureCosmosDBSettings(BaseModelSettings):
    """Azure CosmosDB model settings

    Required:
    - connection_string: str - Azure CosmosDB connection string
        (Env var COSMOSDB_CONNECTION_STRING)
    """

    api: str
    connection_string: SecretStr

    class Config(BaseModelSettings.Config):
        env_prefix = "COSMOSDB_"


class AzureKeyVaultSettings(BaseModelSettings):
    """Azure Key Vault model settings

    Required:
    - vault_url: HttpsUrl - Azure Key Vault URL
        (Env var AZURE_KEY_VAULT_VAULT_URL)
    - client_id: str - Azure Key Vault client ID
        (Env var AZURE_KEY_VAULT_CLIENT_ID)
    - client_secret: SecretStr - Azure Key Vault client secret
        (Env var AZURE_KEY_VAULT_CLIENT_SECRET)
    """

    endpoint: HttpsUrl
    client_id: str
    client_secret: SecretStr

    class Config(BaseModelSettings.Config):
        env_prefix = "AZURE_KEY_VAULT_"


class AstraDBSettings(BaseModelSettings):
    """AstraDB model settings

    Required:
    - app_token: SecretStr - AstraDB token
        (Env var ASTRADB_APP_TOKEN)
    - db_id: str - AstraDB database ID
        (Env var ASTRADB_DB_ID)
    - region: str - AstraDB region
        (Env var ASTRADB_REGION)
    - keyspace: str - AstraDB keyspace
        (Env var ASTRADB_KEYSPACE)
    """

    app_token: SecretStr
    db_id: str
    region: str
    keyspace: str

    class Config(BaseModelSettings.Config):
        env_prefix = "ASTRADB_"


class MongoDBAtlasSettings(BaseModelSettings):
    """MongoDB Atlas model settings

    Required:
    - connection_string: str - MongoDB Atlas connection string
        (Env var MONGODB_ATLAS_CONNECTION_STRING)
    """

    connection_string: SecretStr

    class Config(BaseModelSettings.Config):
        env_prefix = "MONGODB_ATLAS_"


class PineconeSettings(BaseModelSettings):
    """Pinecone model settings

    Required:
    - api_key: SecretStr - Pinecone API key
        (Env var PINECONE_API_KEY)
    """

    api_key: SecretStr

    class Config(BaseModelSettings.Config):
        env_prefix = "PINECONE_"


class PostgresSettings(BaseModelSettings):
    """Postgres model settings

    Required:
    - connection_string: str - Postgres connection string
        (Env var POSTGRES_CONNECTION_STRING)
    """

    connection_string: SecretStr | PostgresDsn

    class Config(BaseModelSettings.Config):
        env_prefix = "POSTGRES_"


class RedisSettings(BaseModelSettings):
    """Redis model settings

    Required:
    - connection_string: str - Redis connection string
        (Env var REDIS_CONNECTION_STRING)
    """

    connection_string: SecretStr

    class Config(BaseModelSettings.Config):
        env_prefix = "REDIS_"


class WeaviateSettings(BaseModelSettings):
    """Weaviate model settings

    Required:
    - url: HttpsUrl - Weaviate URL (Env var WEAVIATE_URL)
    - api_key: SecretStr - Weaviate token (Env var WEAVIATE_API_KEY)
    - use_embed: bool - Whether to use the client embedding options
        (Env var WEAVIATE_USE_EMBED)
    """

    url: HttpsUrl
    api_key: SecretStr
    use_embed: bool = False

    class Config(BaseModelSettings.Config):
        env_prefix = "WEAVIATE_"

    def validate_settings(self):
        if not self.use_embed and not self.url:
            raise ValueError("Weaviate config must have either url or use_embed set")
