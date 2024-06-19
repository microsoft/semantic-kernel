# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class PostgresSettings(KernelBaseSettings):
    """Postgres model settings.

    Args:
    - connection_string: str - Postgres connection string
        (Env var POSTGRES_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "POSTGRES_"

    connection_string: SecretStr
