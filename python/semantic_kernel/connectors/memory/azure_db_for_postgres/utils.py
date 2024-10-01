# Copyright (c) Microsoft. All rights reserved.
import logging

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential

from semantic_kernel.connectors.memory.azure_db_for_postgres.constants import AZURE_DB_FOR_POSTGRES_SCOPE

logger = logging.getLogger(__name__)


async def get_entra_token_aysnc(credential: AsyncTokenCredential) -> str:
    """Get the password from Entra using the provided credential."""
    logger.info("Acquiring Entra token for postgres password")

    async with credential:
        cred = await credential.get_token(AZURE_DB_FOR_POSTGRES_SCOPE)
        return cred.token


def get_entra_token(credential: TokenCredential) -> str:
    """Get the password from Entra using the provided credential."""
    logger.info("Acquiring Entra token for postgres password")

    return credential.get_token(AZURE_DB_FOR_POSTGRES_SCOPE).token
