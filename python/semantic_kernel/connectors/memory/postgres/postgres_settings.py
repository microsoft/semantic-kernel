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
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorConnectionException,
    MemoryConnectorInitializationError,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class PostgresSettings(KernelBaseSettings):
    """Postgres model settings.

    This class is used to configure the Postgres connection pool
    and other settings related to the Postgres store.

    The settings that match what can be configured on tools such as
    psql, pg_dump, pg_restore, pgbench, createdb, and
    `libpq <https://www.postgresql.org/docs/current/libpq-envars.html>`_
    match the environment variables used by those tools. This includes
    PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, and PGSSL_MODE.
    Other settings follow the standard pattern of Pydantic settings,
    e.g. POSTGRES_CONNECTION_STRING.

    Args:
        connection_string: Postgres connection string
        (Env var POSTGRES_CONNECTION_STRING)
        host: Postgres host (Env var PGHOST)
        port: Postgres port (Env var PGPORT)
        dbname: Postgres database name (Env var PGDATABASE)
        user: Postgres user (Env var PGUSER)
        password: Postgres password (Env var PGPASSWORD)
        sslmode: Postgres sslmode (Env var PGSSL_MODE)
            Use "require" to require SSL, "disable" to disable SSL, or "prefer" to prefer
            SSL but allow a connection without it. Defaults to "prefer".
        min_pool: Minimum connection pool size. Defaults to 1.
            (Env var POSTGRES_MIN_POOL)
        max_pool: Maximum connection pool size. Defaults to 5.
            (Env var POSTGRES_MAX_POOL)
        default_dimensionality: Default dimensionality for vectors. Defaults to 100.
            (Env var POSTGRES_DEFAULT_DIMENSIONALITY)
        max_rows_per_transaction: Maximum number of rows to process in a single transaction. Defaults to 1000.
            (Env var POSTGRES_MAX_ROWS_PER_TRANSACTION)
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
    max_rows_per_transaction: int = 1000

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
            raise MemoryConnectorInitializationError("host is required. Please set PGHOST or connection_string.")
        if "dbname" not in result:
            raise MemoryConnectorInitializationError(
                "database is required. Please set PGDATABASE or connection_string."
            )
        if "user" not in result:
            raise MemoryConnectorInitializationError("user is required. Please set PGUSER or connection_string.")
        if "password" not in result:
            raise MemoryConnectorInitializationError(
                "password is required. Please set PGPASSWORD or connection_string."
            )

        return result

    async def create_connection_pool(self) -> AsyncConnectionPool:
        """Creates a connection pool based off of settings."""
        try:
            pool = AsyncConnectionPool(
                min_size=self.min_pool,
                max_size=self.max_pool,
                open=False,
                kwargs=self.get_connection_args(),
            )
            await pool.open()
        except Exception as e:
            raise MemoryConnectorConnectionException("Error creating connection pool.") from e
        return pool
