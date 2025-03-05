# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import ConfigDict, Field, SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureCosmosDBSettings(KernelBaseSettings):
    """Azure CosmosDB model settings.

    Optional:
    - api: str - Azure CosmosDB API version (Env var COSMOSDB_API)
    - connection_string: str - Azure CosmosDB connection string
        (Env var COSMOSDB_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "COSMOSDB_"

    api: str | None = None
    connection_string: SecretStr | None = Field(None, alias="AZCOSMOS_CONNSTR")

    model_config = ConfigDict(
        populate_by_name=True,
    )
