# Copyright (c) Microsoft. All rights reserved.

from typing import Any, ClassVar

from psycopg.conninfo import conninfo_to_dict
from psycopg_pool import AsyncConnectionPool
from pydantic import Field, SecretStr

from semantic_kernel.connectors.memory.postgres.constants import (
    PGDATABASE_ENV_VAR,
    PGHOST_ENV_VAR,
    PGPASSWORD_ENV_VAR,
    PGPORT_ENV_VAR,
    PGSSL_MODE_ENV_VAR,
    PGUSER_ENV_VAR,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class PostgresSettings(KernelBaseSettings):
    """Postgres model settings.

    Args:
    - connection_string: str - Postgres connection string
        (Env var POSTGRES_CONNECTION_STRING)
    - host: str - Postgres host (Env var PGHOST})
    - port: int - Postgres port (Env var PGPORT)
    - dbname: str - Postgres database name (Env var PGDATABASE)
    - user: str - Postgres user (Env var PGUSER)
    - password: str - Postgres password (Env var PGPASSWORD)
    - sslmode: str - Postgres sslmode (Env var PGSSL_MODE)
        Use "require" to require SSL, "disable" to disable SSL, or "prefer" to prefer
        SSL but allow a connection without it. Defaults to "prefer".
    - min_pool: int - Minimum connection pool size. Defaults to 1.
    - max_pool: int - Maximum connection pool size. Defaults to 5.
    - default_dimensionality: int - Default dimensionality for vectors. Defaults to 100.
    """

    env_prefix: ClassVar[str] = "POSTGRES_"

    connection_string: SecretStr | None = None
    host: str | None = Field(None, alias=PGHOST_ENV_VAR)
    port: int | None = Field(5432, alias=PGPORT_ENV_VAR)
    dbname: str | None = Field(None, alias=PGDATABASE_ENV_VAR)
    user: str | None = Field(None, alias=PGUSER_ENV_VAR)
    password: SecretStr | None = Field(None, alias=PGPASSWORD_ENV_VAR)
    sslmode: str | None = Field(None, alias=PGSSL_MODE_ENV_VAR)

    min_pool: int = 1
    max_pool: int = 5

    default_dimensionality: int = 100

    def get_connection_args(self) -> dict[str, Any]:
        """Get connection arguments."""
        result = conninfo_to_dict(self.connection_string.get_secret_value()) if self.connection_string else {}

        if self.host:
            result["host"] = self.host
        if self.port:
            result["port"] = self.port
        if self.dbname:
            result["dbname"] = self.dbname
        if self.user:
            result["user"] = self.user
        if self.password:
            result["password"] = self.password.get_secret_value()

        # Ensure required values
        if "host" not in result:
            raise ValueError("host is required. Please set PGHOST or connection_string.")
        if "dbname" not in result:
            raise ValueError("database is required. Please set PGDATABASE or connection_string.")
        if "user" not in result:
            raise ValueError("user is required. Please set PGUSER or connection_string.")
        if "password" not in result:
            raise ValueError("password is required. Please set PGPASSWORD or connection_string.")

        return result

    async def create_connection_pool(self) -> AsyncConnectionPool:
        """Creates a connection pool based off of settings."""
        pool = AsyncConnectionPool(
            min_size=self.min_pool,
            max_size=self.max_pool,
            open=False,
            kwargs=self.get_connection_args(),
        )
        await pool.open()
        return pool
