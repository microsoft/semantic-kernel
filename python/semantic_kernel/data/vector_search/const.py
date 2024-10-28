# Copyright (c) Microsoft. All rights reserved.


from enum import Enum


class VectorSearchType(str, Enum):
    """Types of vector search queries.

    Attributes:
        SEARCH_STR_RESULT: Search using a query, with result as strings.
        SEARCH_TEXT_SEARCH_RESULT: Search using a query, with result as text search results.
        SEARCH_VECTOR_RESULT: Search using a query, with result as vector search results.
        VECTORIZED_SEARCH: Search with a vector, with result as vector search results.
        VECTORIZABLE_TEXT_SEARCH: Search for a vectorizable text, with result as vector search results.
    """

    SEARCH_STR_RESULT = "search_str_result"
    SEARCH_TEXT_SEARCH_RESULT = "search_text_search_result"
    SEARCH_VECTOR_RESULT = "search_vector_result"
    VECTORIZED_SEARCH = "vectorized_search"
    VECTORIZABLE_TEXT_SEARCH = "vectorizable_text_search"


class TextSearchFunctions(str, Enum):
    """Text search functions.

    Attributes:
        SEARCH: Search using a query.
        GET_TEXT_SEARCH_RESULT: Get text search results.
        GET_SEARCH_RESULT: Get search results.
    """

    SEARCH = "search"
    GET_TEXT_SEARCH_RESULT = "get_text_search_result"
    GET_SEARCH_RESULT = "get_search_result"
