# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings


class MongoDBAtlasSettings(BaseModelSettings):
    """MongoDB Atlas model settings

    Optional:
    - connection_string: str - MongoDB Atlas connection string
        (Env var MONGODB_ATLAS_CONNECTION_STRING)
    """

    connection_string: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "MONGODB_ATLAS_"
