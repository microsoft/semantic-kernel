# Copyright (c) Microsoft. All rights reserved.

import os
from datetime import datetime
from typing import List, Optional, Union

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential as DefaultAzureCredentialSync
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
)
from dotenv import load_dotenv
from numpy import array, linalg, ndarray
from python.semantic_kernel.memory.memory_record import MemoryRecord


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
        if acs_key is None:
            raise ValueError(
                "No Azure Cognitive Search Key found; Please provide API key AZURE_SEARCH_ADMIN_KEY env variable."
            )
        else:
            credential = AzureKeyCredential(acs_key)
    return credential


def acs_schema(vector_size: int) -> list:
    """Creates an ACS schema for collection/index creation.

    Arguments:
        vector_size {int} -- The size of the vectors being stored in collection/index.

    Returns:
        list -- The ACS schema as list type.
    """

    acs_fields = [
        SimpleField(
            name="vector_id",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            retrievable=True,
            key=True,
        ),
        SearchableField(
            name="timestamp",
            type=SearchFieldDataType.DateTimeOffset,
            searchable=True,
            retrievable=True,
        ),
        SearchableField(
            name="payload",
            type=SearchFieldDataType.String,
            filterable=True,
            searchable=True,
            retrievable=True,
        ),
        SearchableField(
            name="additional_metadata",
            type=SearchFieldDataType.String,
            filterable=True,
            searchable=True,
            retrievable=True,
        ),
        SearchField(
            name="vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            dimensions=vector_size,
            vector_search_configuration="az-vector-config",
        ),
    ]

    return acs_fields


def acs_field_selection(include_embedding: bool) -> List[str]:
    """Creates a field selection string for ACS search.

    Arguments:
        with_embedding {bool} -- Whether to include the embedding field in the selection.

    Returns:
        str -- The field selection string.
    """
    if include_embedding:
        select_fields = [
            "vector_id",
            "timestamp",
            "vector",
            "payload",
            "additional_metadata",
        ]
    else:
        select_fields = ["vector_id", "timestamp", "payload", "additional_metadata"]

    return select_fields


def convert_to_memory_record(acs_data: dict, include_embedding: bool) -> MemoryRecord:
    """Converts a search result to a MemoryRecord.

    Arguments:
        acs_data {dict} -- ACS result data.

    Returns:
        MemoryRecord -- The MemoryRecord from ACS Data Result.
    """
    sk_result = MemoryRecord(
        is_reference=False,
        external_source_name="azure-cognitive-search",
        key=None,
        timestamp=acs_data["timestamp"]
        if not acs_data["timestamp"]
        else datetime.datetime.now().timestamp(),
        id=acs_data["vector_id"],
        embedding=acs_data["vector"] if include_embedding else None,
        text=acs_data["payload"],
        additional_metadata=acs_data["additional_metadata"],
    )
    return sk_result


def compute_similarity_scores(
    self, embedding: ndarray, embedding_array: ndarray
) -> ndarray:
    """Computes the cosine similarity scores between a query embedding and a group of embeddings.

    Arguments:
        embedding {ndarray} -- The query embedding.
        embedding_array {ndarray} -- The group of embeddings.

    Returns:
        ndarray -- The cosine similarity scores.
    """
    query_norm = linalg.norm(embedding)
    collection_norm = linalg.norm(embedding_array, axis=1)

    # Compute indices for which the similarity scores can be computed
    valid_indices = (query_norm != 0) & (collection_norm != 0)

    # Initialize the similarity scores with -1 to distinguish the cases
    # between zero similarity from orthogonal vectors and invalid similarity
    similarity_scores = array([-1.0] * embedding_array.shape[0])

    if valid_indices.any():
        similarity_scores[valid_indices] = embedding.dot(
            embedding_array[valid_indices].T
        ) / (query_norm * collection_norm[valid_indices])
        if not valid_indices.all():
            self._logger.warning(
                "Some vectors in the embedding collection are zero vectors."
                "Ignoring cosine similarity score computation for those vectors."
            )
    else:
        raise ValueError(
            f"Invalid vectors, cannot compute cosine similarity scores"
            f"for zero vectors"
            f"{embedding_array} or {embedding}"
        )
    return similarity_scores
