# Copyright (c) Microsoft. All rights reserved.
import sys
from typing import Any

from psycopg.conninfo import conninfo_to_dict
from psycopg_pool import AsyncConnectionPool
from pydantic import Field, SecretStr

from semantic_kernel.connectors.memory.azure_db_for_postgres.constants import (
    AZURE_DB_FOR_POSTGRES_CONNECTION_STRING_ENV_VAR,
)
from semantic_kernel.connectors.memory.azure_db_for_postgres.entra_connection import AsyncEntraConnection
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError

if sys.version_info >= (3, 12):
    pass  # pragma: no cover
else:
    pass  # pragma: no cover

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential

from semantic_kernel import __version__
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings


class AzureDBForPostgresSettings(PostgresSettings):
    """Azure DB for Postgres model settings.

    This is the same as PostgresSettings, but does not a require a password.
    If a password is not supplied, then Entra will use the Azure AD token.
    You can also supply an Azure credential directly.
    """

    credential: AsyncTokenCredential | TokenCredential | None = None

    azure_db_connection_string: SecretStr | None = Field(None, alias=AZURE_DB_FOR_POSTGRES_CONNECTION_STRING_ENV_VAR)
    """A azure db specific connection string. Can be supplied instead of POSTGRES_CONNECTION_STRING
    
    This is useful if settings for both an Azure DB and a regular Postgres database are needed.
    """

    def get_connection_args(self, **kwargs) -> dict[str, Any]:
        """Get connection arguments.

        Args:
            kwargs: dict[str, Any] - Additional arguments
                Use this to override any connection arguments.

        Returns:
            dict[str, Any]: Connection arguments that can be passed to psycopg.connect
        """
        conn_string_setting = self.azure_db_connection_string or self.connection_string
        result = conninfo_to_dict(conn_string_setting.get_secret_value()) if conn_string_setting else {}

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

        result = {**result, **kwargs}

        # Ensure required values
        if "host" not in result:
            raise MemoryConnectorInitializationError("host is required. Please set PGHOST or connection_string.")
        if "dbname" not in result:
            raise MemoryConnectorInitializationError(
                "database is required. Please set PGDATABASE or connection_string."
            )

        return result

    async def create_connection_pool(self) -> AsyncConnectionPool:
        """Creates a connection pool based off of settings.

        Uses AsyncEntraConnection as the connection class, which
        can set the user and password based on a Entra token.
        """
        pool: AsyncConnectionPool = AsyncConnectionPool(
            min_size=self.min_pool,
            max_size=self.max_pool,
            open=False,
            kwargs={
                **self.get_connection_args(),
                **{
                    "credential": self.credential,
                    "application_name": f"semantic_kernel (python) v{__version__}",
                },
            },
            connection_class=AsyncEntraConnection,
        )
        await pool.open()
        return pool
