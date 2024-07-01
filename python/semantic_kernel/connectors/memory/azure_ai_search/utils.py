# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.search.documents.indexes.aio import SearchIndexClient

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.exceptions import ServiceInitializationError

if TYPE_CHECKING:
    from azure.core.credentials_async import AsyncTokenCredential


def get_search_index_async_client(
    azure_ai_search_settings: AzureAISearchSettings,
    azure_credential: AzureKeyCredential | None = None,
    token_credential: "AsyncTokenCredential | TokenCredential | None" = None,
):
    """Return a client for Azure Cognitive Search.

    Args:
        azure_ai_search_settings (AzureAISearchSettings): Azure Cognitive Search settings.
        azure_credential (AzureKeyCredential): Optional Azure credentials (default: {None}).
        token_credential (TokenCredential): Optional Token credential (default: {None}).
    """
    # Credentials
    credential: "AzureKeyCredential | AsyncTokenCredential | TokenCredential | None" = None
    if azure_ai_search_settings.api_key:
        credential = AzureKeyCredential(azure_ai_search_settings.api_key.get_secret_value())
    elif azure_credential:
        credential = azure_credential
    elif token_credential:
        credential = token_credential
    else:
        raise ServiceInitializationError("Error: missing Azure Cognitive Search client credentials.")

    if not credential:
        raise ServiceInitializationError("Error: Azure Cognitive Search credentials not set.")

    return SearchIndexClient(
        endpoint=str(azure_ai_search_settings.endpoint),
        credential=credential,
        headers={USER_AGENT: "Semantic-Kernel"},
    )
