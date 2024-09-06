# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.data.text_search import TextSearch
from semantic_kernel.data.text_search_options import TextSearchOptions


class KernelSearchExtension:
    """Extension for the kernel search service."""

    def create_function_from_search(self, search: TextSearch, options: TextSearchOptions) -> callable:
        """Create a function from a search service."""

        async def search_function(query: str):
            return await search.search(query, options)

        return search_function
