# Copyright (c) Microsoft. All rights reserved.


from typing import Literal

from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.data.vector_search.const import VectorSearchQueryTypes
from semantic_kernel.data.vector_search.vector_search_filter import VectorSearchFilter
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorSearchOptions(TextSearchOptions):
    """Options for vector search, builds on TextSearchOptions."""

    filter: VectorSearchFilter | None = None
    vector: list[float | int] | None = None
    vector_field_name: str | None = None
    include_vectors: bool = False
    select_fields: list[str] | None = None
    query_type: Literal[
        VectorSearchQueryTypes.VECTORIZED_SEARCH_QUERY,
        VectorSearchQueryTypes.VECTORIZABLE_TEXT_SEARCH_QUERY,
        VectorSearchQueryTypes.HYBRID_TEXT_VECTORIZED_SEARCH_QUERY,
        VectorSearchQueryTypes.HYBRID_VECTORIZABLE_TEXT_SEARCH_QUERY,
    ] = VectorSearchQueryTypes.VECTORIZABLE_TEXT_SEARCH_QUERY
