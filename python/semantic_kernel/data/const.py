# Copyright (c) Microsoft. All rights reserved.


from enum import Enum


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


class FilterClauseType(str, Enum):
    """Types of filter clauses for vector search queries."""

    EQUALITY = "equality"
    TAG_LIST_CONTAINS = "tag_list_contains"
