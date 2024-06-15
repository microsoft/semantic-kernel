# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RedisSettings(KernelBaseSettings):
    """Redis model settings.

    Args:
    - connection_string (str | None):
        Redis connection string (Env var REDIS_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "REDIS_"

    connection_string: SecretStr
