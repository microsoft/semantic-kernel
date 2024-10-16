# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import HttpUrl, SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureCosmosDBNoSQLSettings(KernelBaseSettings):
    """Azure CosmosDB NoSQL settings.

    The settings are first loaded from environment variables with
    the prefix 'COSMOS_DB_NOSQL_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'COSMOS_DB_NOSQL_':
    - url: HttpsUrl - The uri of the Azure CosmosDB NoSQL account.
           This value can be found in the Keys & Endpoint section when examining
           your resource from the Azure portal.
           (Env var name: COSMOS_DB_NOSQL_URL)

    Optional settings for prefix 'COSMOS_DB_NOSQL_':
    - key: SecretStr - The primary key of the Azure CosmosDB NoSQL account.
           This value can be found in the Keys & Endpoint section when examining
           your resource from the Azure portal.
           (Env var name: COSMOS_DB_NOSQL_KEY)
    """

    env_prefix: ClassVar[str] = "COSMOS_DB_NOSQL_"

    url: HttpUrl
    key: SecretStr | None = None
