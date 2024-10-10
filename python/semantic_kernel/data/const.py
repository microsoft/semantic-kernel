# Copyright (c) Microsoft. All rights reserved.


from enum import Enum
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
from typing import Final
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from typing import Final
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
from typing import Final
>>>>>>> main
>>>>>>> Stashed changes


class IndexKind(str, Enum):
    """Index kinds for similarity search."""

    HNSW = "hnsw"
    FLAT = "flat"


class DistanceFunction(str, Enum):
    """Distance functions for similarity search."""

    COSINE = "cosine"
    DOT_PROD = "dot_prod"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes


class VectorSearchQueryTypes(str, Enum):
    """Types of vector search queries.

    Attributes:
        VECTORIZED_SEARCH_QUERY: A type of query that searches a vector store using a vector.
        VECTORIZABLE_TEXT_SEARCH_QUERY: A type of query that search a vector store using a
            text string that will be vectorized downstream.
        HYBRID_TEXT_VECTORIZED_SEARCH_QUERY: A type of query that does a hybrid search in
            a vector store using a vector and text.
        HYBRID_VECTORIZABLE_TEXT_SEARCH_QUERY: A type of query that does a hybrid search
            using a text string that will be vectorized downstream.
    """

    VECTORIZED_SEARCH_QUERY = "vectorized_search_query"
    VECTORIZABLE_TEXT_SEARCH_QUERY = "vectorizable_text_search_query"
    HYBRID_TEXT_VECTORIZED_SEARCH_QUERY = "hybrid_text_vectorized_search_query"
    HYBRID_VECTORIZABLE_TEXT_SEARCH_QUERY = "hybrid_vectorizable_text_search_query"


DEFAULT_DESCRIPTION: Final[str] = (
    "Perform a search for content related to the specified query and return string results"
)
DEFAULT_COUNT: Final[int] = 5
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
