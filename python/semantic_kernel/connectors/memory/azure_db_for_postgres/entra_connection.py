# Copyright (c) Microsoft. All rights reserved.
import base64
import json
import logging
from functools import lru_cache

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity import DefaultAzureCredential
from psycopg import AsyncConnection

from semantic_kernel.connectors.memory.azure_db_for_postgres.constants import AZURE_DB_FOR_POSTGRES_SCOPE

logger = logging.getLogger(__name__)


async def get_entra_token_aysnc(credential: AsyncTokenCredential) -> str:
    """Get the password from Entra using the provided credential."""
    logger.info("Acquiring Entra token for postgres password")

    async with credential:
        cred = await credential.get_token(AZURE_DB_FOR_POSTGRES_SCOPE)
        return cred.token


def get_entra_token(credential: TokenCredential | None) -> str:
    """Get the password from Entra using the provided credential."""
    logger.info("Acquiring Entra token for postgres password")
    credential = credential or get_default_azure_credentials()

    return credential.get_token(AZURE_DB_FOR_POSTGRES_SCOPE).token


@lru_cache(maxsize=1)
def get_default_azure_credentials() -> DefaultAzureCredential:
    """Get the default Azure credentials.

    This method caches the credentials to avoid creating new instances.
    """
    return DefaultAzureCredential()


def decode_jwt(token):
    """Decode the JWT payload to extract claims."""
    payload = token.split(".")[1]
    padding = "=" * (4 - len(payload) % 4)
    decoded_payload = base64.urlsafe_b64decode(payload + padding)
    return json.loads(decoded_payload)


async def get_entra_conninfo(credential: TokenCredential | AsyncTokenCredential | None) -> dict[str, str]:
    """Fetches a token returns the username and token."""
    # Fetch a new token and extract the username
    if isinstance(credential, AsyncTokenCredential):
        token = await get_entra_token_aysnc(credential)
    else:
        token = get_entra_token(credential)
    claims = decode_jwt(token)
    username = claims.get("upn") or claims.get("preferred_username") or claims.get("unique_name")
    if not username:
        raise ValueError("Could not extract username from token. Have you logged in?")

    return {"user": username, "password": token}


class AsyncEntraConnection(AsyncConnection):
    """Asynchronous connection class for using Entra auth with Azure DB for PostgreSQL."""

    @classmethod
    async def connect(cls, *args, **kwargs):
        """Establish an asynchronous connection using Entra auth with Azure DB for PostgreSQL."""
        credential = kwargs.pop("credential", None)
        if credential and not isinstance(credential, (TokenCredential, AsyncTokenCredential)):
            raise ValueError("credential must be a TokenCredential or AsyncTokenCredential")
        if credential or not kwargs.get("user") or not kwargs.get("password"):
            entra_conninfo = await get_entra_conninfo(credential)
            kwargs["password"] = entra_conninfo["password"]
            if not kwargs.get("user"):
                # If user isn't already set, use the username from the token
                kwargs["user"] = entra_conninfo["user"]
        return await super().connect(*args, **kwargs | entra_conninfo)
