# Copyright (c) Microsoft. All rights reserved.

import os
from typing import Optional, Union
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential as DefaultAzureCredentialSync
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SemanticConfiguration,
    PrioritizedFields,
    SemanticField,
    SemanticSettings,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
)


def create_credentials(
    use_async: bool, azsearch_api_key: Optional[str] = None
) -> Union[AzureKeyCredential, DefaultAzureCredential, DefaultAzureCredentialSync]:
    load_dotenv()
    acs_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")

    if azsearch_api_key:
        credential = (
            DefaultAzureCredential() if use_async else DefaultAzureCredentialSync()
        )
    else:
        credential = AzureKeyCredential(acs_key)
    return credential
