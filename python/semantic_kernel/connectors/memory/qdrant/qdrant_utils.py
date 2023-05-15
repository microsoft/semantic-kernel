# Copyright (c) Microsoft. All rights reserved.

import uuid
from numpy import array, linalg, ndarray, zeros
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from semantic_kernel.memory.memory_record import MemoryRecord

from typing import Optional

"""
Utility function(s) for Qdrant vector database to support Qdrant Semantic Kernel memory implementation.
"""

def guid_comb_generator() -> str:  
    """
    Generate a GUID-comb identifier.

    Returns:
        str: A GUID-comb identifier.
    """
    
    return str(uuid.uuid4())

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


def convert_from_memory_record(
          qdrant_client: QdrantClient, collection_name: str, 
          record: MemoryRecord, vector_size: Optional[int] = 0
    ) -> dict:
        """Converts a memory record to a Qdrant vector record.
           Added to be in parity with C# Semantic Kernel implementation.

        Arguments:
            qdrant_client {QdrantClient} -- The connected Qdrant client.
            collection_name {str} -- The name of the collection.
            record {MemoryRecord} -- The memory record.

        Returns:
            Tuple[string, List[ScoredPoint]] --  Converted record to Tuple of 
            str: Collection name and ScoredQdrant vector record.
        """
        point_id = str()

        if record.key: 
            point_id = record.key
        else:
            if vector_size == 0:
                collection_info = qdrant_client.get_collection(
                    collection_name=collection_name
                )

            vector_size = collection_info.config.params.vectors.size
            search_vector = zeros(vector_size)

            vector_data = qdrant_client.search(
                collection_name=collection_name,
                query_vector=search_vector, 
                query_filter= Filter(
                    must=[
                        FieldCondition(
                            key="id",
                            match=MatchValue(value=record.metadata.id),
                        )
                    ]
                ),
                limit=1
            ) 

            if vector_data:
               point_id = str(vector_data[0].id)
            else:
                point_id = uuid.uuid4()  
                id=[str(point_id)]                 
                vector_data = qdrant_client.retrieve(
                    collection_name=collection_name,
                    ids=id,
                )
                while vector_data:
                    point_id = uuid.uuid4()  
                    id=[str(point_id)]                 
                    vector_data = qdrant_client.retrieve(
                        collection_name=collection_name,
                        ids=id,
                    )
            
        result = dict(
                    collectionname = collection_name,
                    pointid = point_id, 
                    vector = record.embedding, 
                    payload = record.payload
            )

        return result