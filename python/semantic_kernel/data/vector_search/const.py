# Copyright (c) Microsoft. All rights reserved.


from enum import Enum


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
