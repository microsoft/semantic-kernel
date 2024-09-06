# Copyright (c) Microsoft. All rights reserved.


from typing import Literal

from semantic_kernel.data.const import VectorSearchQueryTypes
from semantic_kernel.data.filters.vector_search_filter import VectorSearchFilter
from semantic_kernel.data.text_search_options import TextSearchOptions


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
