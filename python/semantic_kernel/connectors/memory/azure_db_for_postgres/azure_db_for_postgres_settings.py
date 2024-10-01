# Copyright (c) Microsoft. All rights reserved.
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity import DefaultAzureCredential
from psycopg.conninfo import conninfo_to_dict

from semantic_kernel.connectors.memory.azure_db_for_postgres.utils import get_entra_token, get_entra_token_aysnc
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings


class AzureDBForPostgresSettings(PostgresSettings):
    """Azure DB for Postgres model settings.

    This is the same as PostgresSettings, but does not a require a password.
    If a password is not supplied, then Entra will use the Azure AD token.
    You can also supply an Azure credential directly.
    """

    credential: AsyncTokenCredential | TokenCredential | None = None

    @override
    def get_connection_args(self, **kwargs) -> dict[str, Any]:
        """Get connection arguments."""
        password: Any = self.password.get_secret_value() if self.password else None
        if not password and self.connection_string:
            password = conninfo_to_dict(self.connection_string.get_secret_value()).get("password")

        if not password:
            self.credential = self.credential or DefaultAzureCredential()
            if isinstance(self.credential, AsyncTokenCredential):
                password = get_entra_token_aysnc(self.credential)
            else:
                password = get_entra_token(self.credential)

        return super().get_connection_args(password=password)
