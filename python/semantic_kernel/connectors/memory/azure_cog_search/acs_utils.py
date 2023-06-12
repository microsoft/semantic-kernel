# Copyright (c) Microsoft. All rights reserved.

import os
from typing import Optional, Union
from dotenv import load_dotenv
from numpy import linalg
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential as DefaultAzureCredentialSync
from azure.identity.aio import DefaultAzureCredential

from numpy import array, ndarray


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

def acs_schema() -> list:
    
    fields = [
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
            SearchField(
                name="vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                dimensions=vector_size,
                vector_search_configuration="az-vector-config",
            ),
        ]
    
    return fields

def convert_to_memory_record() -> None:
    return

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
