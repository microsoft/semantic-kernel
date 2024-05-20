# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings


class RedisSettings(BaseModelSettings):
    """Redis model settings

    Optional:
    - connection_string: str | None - Redis connection string
        (Env var REDIS_CONNECTION_STRING)
    """

    connection_string: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "REDIS_"
