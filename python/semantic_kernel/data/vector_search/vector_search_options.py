# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.data.vector_search.vector_search_filter import VectorSearchFilter
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorSearchOptions(TextSearchOptions):
    """Options for vector search, builds on TextSearchOptions."""

    filter: VectorSearchFilter | None = None
    vector_field_name: str | None = None
    include_vectors: bool = False
    include_total_count: bool = False
