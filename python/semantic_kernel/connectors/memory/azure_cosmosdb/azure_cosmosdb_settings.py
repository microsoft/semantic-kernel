# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings


class AzureCosmosDBSettings(BaseModelSettings):
    """Azure CosmosDB model settings

    Optional:
    - connection_string: str - Azure CosmosDB connection string
        (Env var COSMOSDB_CONNECTION_STRING)
    """

    api: str | None = None
    connection_string: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "COSMOSDB_"
