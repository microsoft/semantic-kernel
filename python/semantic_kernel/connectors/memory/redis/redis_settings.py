# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RedisSettings(BaseModelSettings):
    """Redis model settings.

    Args:
    - connection_string (str | None):
        Redis connection string (Env var REDIS_CONNECTION_STRING)
    """

    connection_string: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        """Model configuration."""

        env_prefix = "REDIS_"
