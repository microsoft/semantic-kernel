# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureCosmosDBSettings(BaseModelSettings):
    """Azure CosmosDB model settings.

    Args:
    - connection_string: str - Azure CosmosDB connection string
        (Env var COSMOSDB_CONNECTION_STRING)
    """

    api: str | None = None
    connection_string: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        """Pydantic configuration settings."""

        env_prefix = "COSMOSDB_"
