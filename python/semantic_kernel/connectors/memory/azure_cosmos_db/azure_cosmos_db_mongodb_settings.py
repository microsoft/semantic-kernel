# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.connectors.memory.mongodb_atlas.const import DEFAULT_DB_NAME
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureCosmosDBforMongoDBSettings(KernelBaseSettings):
    """Azure CosmosDB for MongoDB settings.

    The settings are first loaded from environment variables with
    the prefix 'AZURE_COSMOS_DB_MONGODB_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'AZURE_COSMOS_DB_MONGODB_':
    - connection_string:  The connection string of the Azure CosmosDB for MongoDB account.
       This value can be found in the Keys & Endpoint section when examining
       your resource from the Azure portal.
       (Env var name: AZURE_COSMOS_DB_MONGODB_CONNECTION_STRING)
    - database_name: str - The name of the database. Please refer to this documentation
       on Azure CosmosDB NoSQL resource model:
       https://learn.microsoft.com/en-us/azure/cosmos-db/resource-model
       (Env var name: AZURE_COSMOS_DB_MONGODB_DATABASE_NAME)
    """

    env_prefix: ClassVar[str] = "AZURE_COSMOS_DB_MONGODB_"

    connection_string: SecretStr | None = None
    database_name: str = DEFAULT_DB_NAME
