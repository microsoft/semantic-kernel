# Copyright (c) Microsoft. All rights reserved.

import base64
import os
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
)
from dotenv import load_dotenv

from semantic_kernel.memory.memory_record import MemoryRecord

SEARCH_FIELD_ID = "Id"
SEARCH_FIELD_TEXT = "Text"
SEARCH_FIELD_EMBEDDING = "Embedding"
SEARCH_FIELD_SRC = "ExternalSourceName"
SEARCH_FIELD_DESC = "Description"
SEARCH_FIELD_METADATA = "AdditionalMetadata"
SEARCH_FIELD_IS_REF = "IsReference"


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


def get_index_schema(vector_size: int) -> list:
    """Return the schema of search indexes.

    Arguments:
        vector_size {int} -- The size of the vectors being stored in collection/index.

    Returns:
        list -- The Azure Cognitive Search schema as list type.
    """

    search_fields = [
        SimpleField(
            name=SEARCH_FIELD_ID,
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True,
            key=True,
        ),
        SearchableField(
            name=SEARCH_FIELD_TEXT,
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True,
        ),
        SearchField(
            name=SEARCH_FIELD_EMBEDDING,
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=vector_size,
            vector_search_configuration="az-vector-config",
        ),
        SimpleField(
            name=SEARCH_FIELD_SRC,
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name=SEARCH_FIELD_DESC,
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name=SEARCH_FIELD_METADATA,
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True,
        ),
        SimpleField(
            name=SEARCH_FIELD_IS_REF,
            type=SearchFieldDataType.Boolean,
            searchable=True,
            filterable=True,
            retrievable=True,
        ),
    ]

    return search_fields


def get_field_selection(with_embeddings: bool) -> List[str]:
    """Get the list of fields to search and load.

    Arguments:
        with_embedding {bool} -- Whether to include the embedding vector field.

    Returns:
        List[str] -- List of fields.
    """

    field_selection = [
        SEARCH_FIELD_ID,
        SEARCH_FIELD_TEXT,
        SEARCH_FIELD_SRC,
        SEARCH_FIELD_DESC,
        SEARCH_FIELD_METADATA,
        SEARCH_FIELD_IS_REF,
    ]

    if with_embeddings:
        field_selection.append(SEARCH_FIELD_EMBEDDING)

    return field_selection


def dict_to_memory_record(data: dict, with_embeddings: bool) -> MemoryRecord:
    """Converts a search result to a MemoryRecord.

    Arguments:
        data {dict} -- Azure Cognitive Search result data.

    Returns:
        MemoryRecord -- The MemoryRecord from Azure Cognitive Search Data Result.
    """

    sk_result = MemoryRecord(
        id=decode_id(data[SEARCH_FIELD_ID]),
        key=data[SEARCH_FIELD_ID],
        text=data[SEARCH_FIELD_TEXT],
        external_source_name=data[SEARCH_FIELD_SRC],
        description=data[SEARCH_FIELD_DESC],
        additional_metadata=data[SEARCH_FIELD_METADATA],
        is_reference=data[SEARCH_FIELD_IS_REF],
        embedding=data[SEARCH_FIELD_EMBEDDING] if with_embeddings else None,
        timestamp=None,
    )
    return sk_result


def memory_record_to_search_record(record: MemoryRecord) -> dict:
    """Convert a MemoryRecord to a dictionary

    Arguments:
        record {MemoryRecord} -- The MemoryRecord from Azure Cognitive Search Data Result.

    Returns:
        data {dict} -- Dictionary data.
    """

    return {
        SEARCH_FIELD_ID: encode_id(record._id),
        SEARCH_FIELD_TEXT: str(record._text),
        SEARCH_FIELD_SRC: record._external_source_name or "",
        SEARCH_FIELD_DESC: record._description or "",
        SEARCH_FIELD_METADATA: record._additional_metadata or "",
        SEARCH_FIELD_IS_REF: str(record._is_reference),
        SEARCH_FIELD_EMBEDDING: record._embedding.tolist(),
    }


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
