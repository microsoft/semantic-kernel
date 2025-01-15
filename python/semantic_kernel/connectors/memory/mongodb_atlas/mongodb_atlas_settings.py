# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, ClassVar

from pydantic import Field, SecretStr

from semantic_kernel.connectors.memory.mongodb_atlas.const import DEFAULT_DB_NAME, DEFAULT_SEARCH_INDEX_NAME
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class MongoDBAtlasSettings(KernelBaseSettings):
    """MongoDB Atlas model settings.

    Args:
    - connection_string: str - MongoDB Atlas connection string
        (Env var MONGODB_ATLAS_CONNECTION_STRING)
    - database_name: str - MongoDB Atlas database name, defaults to 'default'
    """

    env_prefix: ClassVar[str] = "MONGODB_ATLAS_"

    connection_string: SecretStr
    database_name: str = DEFAULT_DB_NAME
    index_name: Annotated[str, Field(deprecated="This field is not used with the new store and collection")] = (
        DEFAULT_SEARCH_INDEX_NAME
    )
