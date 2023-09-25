# Copyright (c) Microsoft. All rights reserved.

import base64
import os
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential, TokenCredential
from dotenv import load_dotenv

SEARCH_FIELD_ID_KEY = "SEARCH_FIELD_ID"
SEARCH_FIELD_TEXT_KEY = "SEARCH_FIELD_TEXT"
SEARCH_FIELD_EMBEDDING_KEY = "SEARCH_FIELD_EMBEDDING"
SEARCH_FIELD_SRC_KEY = "SEARCH_FIELD_SRC"
SEARCH_FIELD_DESC_KEY = "SEARCH_FIELD_DESC"
SEARCH_FIELD_METADATA_KEY = "SEARCH_FIELD_METADATA"
SEARCH_FIELD_IS_REF_KEY = "SEARCH_FIELD_IS_REF"

def get_search_index_async_client(
    search_endpoint: Optional[str] = None,
    admin_key: Optional[str] = None,
    azure_credential: Optional[AzureKeyCredential] = None,
    token_credential: Optional[TokenCredential] = None,
):
    """Return a client for Azure Cognitive Search.

    Arguments:
        search_endpoint {str}                 -- Optional endpoint (default: {None}).
        admin_key {str}                       -- Optional API key (default: {None}).
        azure_credential {AzureKeyCredential} -- Optional Azure credentials (default: {None}).
        token_credential {TokenCredential}    -- Optional Token credential (default: {None}).
    """

    ENV_VAR_ENDPOINT = "AZURE_COGNITIVE_SEARCH_ENDPOINT"
    ENV_VAR_API_KEY = "AZURE_COGNITIVE_SEARCH_ADMIN_KEY"

    try:
        # Note: there are two client classes available:
        # 1. Async: azure.search.documents.indexes.aio.SearchIndexClient
        # 2. Sync: azure.search.documents.indexes.SearchIndexClient
        from azure.search.documents.indexes.aio import SearchIndexClient
    except ImportError:
        raise ValueError(
            "Error: Unable to import Azure Cognitive Search client python package."
            "Please install Azure Cognitive Search client"
        )

    # Load environment variables
    load_dotenv()

    # Service endpoint
    if search_endpoint:
        service_endpoint = search_endpoint
    elif os.getenv(ENV_VAR_ENDPOINT):
        service_endpoint = os.getenv(ENV_VAR_ENDPOINT)
    else:
        raise ValueError("Error: missing Azure Cognitive Search client endpoint.")

    if service_endpoint is None:
        print(service_endpoint)
        raise ValueError("Error: Azure Cognitive Search client not set.")

    # Credentials
    if admin_key:
        azure_credential = AzureKeyCredential(admin_key)
    elif azure_credential:
        azure_credential = azure_credential
    elif token_credential:
        token_credential = token_credential
    elif os.getenv(ENV_VAR_API_KEY):
        azure_credential = AzureKeyCredential(os.getenv(ENV_VAR_API_KEY))
    else:
        raise ValueError("Error: missing Azure Cognitive Search client credentials.")

    if azure_credential is None and token_credential is None:
        raise ValueError("Error: Azure Cognitive Search credentials not set.")

    sk_headers = {"User-Agent": "Semantic-Kernel"}

    if azure_credential:
        return SearchIndexClient(
            endpoint=service_endpoint, credential=azure_credential, headers=sk_headers
        )

    if token_credential:
        return SearchIndexClient(
            endpoint=service_endpoint, credential=token_credential, headers=sk_headers
        )

    raise ValueError("Error: unable to create Azure Cognitive Search client.")


def encode_id(id: str) -> str:
    """Encode a record id to ensure compatibility with Azure Cognitive Search.

    Azure Cognitive Search keys can contain only letters, digits, underscore, dash,
    equal sign, recommending to encode values with a URL-safe algorithm.
    """

    id_bytes = id.encode("ascii")
    base64_bytes = base64.b64encode(id_bytes)
    return base64_bytes.decode("ascii")


def decode_id(base64_id: str) -> str:
    """Decode a record id to the original value.

    Azure Cognitive Search keys can contain only letters, digits, underscore, dash,
    equal sign, recommending to encode values with a URL-safe algorithm.
    """

    base64_bytes = base64_id.encode("ascii")
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode("ascii")
