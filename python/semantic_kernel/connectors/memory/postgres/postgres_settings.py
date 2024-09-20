# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from psycopg.conninfo import conninfo_to_dict
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

    connection_string: SecretStr | None = None
    host: str | None = None
    port: int | None = None
    dbname: str | None = None
    user: str | None = None
    password: SecretStr | None = None
    sslmode: str | None = None

    min_pool: int = 1
    max_pool: int = 5

    default_dimensionality: int = 100

    def get_connection_args(self) -> dict[str, str]:
        """Get connection arguments."""
        result = conninfo_to_dict(self.connection_string.get_secret_value()) if self.connection_string else {}

        if self.host:
            result["host"] = self.host
        if self.port:
            result["port"] = self.port
        if self.dbname:
            result["database"] = self.dbname
        if self.user:
            result["user"] = self.user
        if self.password:
            result["password"] = self.password.get_secret_value()

        return result
