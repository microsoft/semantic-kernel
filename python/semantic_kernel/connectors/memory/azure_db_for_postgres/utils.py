# Copyright (c) Microsoft. All rights reserved.
import logging
from functools import lru_cache

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity import DefaultAzureCredential

from semantic_kernel.connectors.memory.azure_db_for_postgres.constants import AZURE_DB_FOR_POSTGRES_SCOPE

logger = logging.getLogger(__name__)


async def get_entra_token_async(credential: AsyncTokenCredential) -> str:
    """Get the password from Entra using the provided credential."""
    logger.info("Acquiring Entra token for postgres password")

    async with credential:
        cred = await credential.get_token(AZURE_DB_FOR_POSTGRES_SCOPE)
        return cred.token


def get_entra_token(credential: TokenCredential | None) -> str:
    """Get the password from Entra using the provided credential."""
    logger.info("Acquiring Entra token for postgres password")
    credential = credential or get_default_azure_credentials()
    print("HERE")

    return credential.get_token(AZURE_DB_FOR_POSTGRES_SCOPE).token


@lru_cache(maxsize=1)
def get_default_azure_credentials() -> DefaultAzureCredential:
    """Get the default Azure credentials.

    This method caches the credentials to avoid creating new instances.
    """
    return DefaultAzureCredential()
