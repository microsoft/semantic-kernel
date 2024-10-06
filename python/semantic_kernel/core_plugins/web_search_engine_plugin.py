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
<<<<<<< main
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
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function

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
=======
import sys
from typing import TYPE_CHECKING, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function

>>>>>>> ms/small_fixes
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
if TYPE_CHECKING:
    from semantic_kernel.connectors.search_engine.connector import ConnectorBase


class WebSearchEnginePlugin:
    """A plugin that provides web search engine functionality.

    Usage:
        connector = BingConnector(bing_search_api_key)
        kernel.add_plugin(WebSearchEnginePlugin(connector), plugin_name="WebSearch")

    Examples:
        {{WebSearch.search "What is semantic kernel?"}}
        =>  Returns the first `num_results` number of results for the given search query
            and ignores the first `offset` number of results.
    """

    _connector: "ConnectorBase"

    def __init__(self, connector: "ConnectorBase") -> None:
        """Initializes a new instance of the WebSearchEnginePlugin class."""
        self._connector = connector

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
<<<<<<< main
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
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
    @kernel_function(
        name="search", description="Performs a web search for a given query"
    )
    async def search(
        self,
        query: Annotated[str, "The search query"],
        num_results: Annotated[int, "The number of search results to return"] = 1,
        offset: Annotated[int, "The number of search results to skip"] = 0,
    ) -> list[str]:
        """Returns the search results of the query provided."""
        return await self._connector.search(query, num_results, offset)
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
=======
    @kernel_function(description="Performs a web search for a given query", name="search")
    async def search(
        self,
        query: Annotated[str, "The search query"],
        num_results: Annotated[Optional[int], "The number of search results to return"] = 1,
        offset: Annotated[Optional[int], "The number of search results to skip"] = 0,
    ) -> str:
        """
        Returns the search results of the query provided.
        Returns `num_results` results and ignores the first `offset`.

        :param query: search query
        :param num_results: number of search results to return, default is 1
        :param offset: number of search results to skip, default is 0
        :return: stringified list of search results
        """
        result = await self._connector.search(query, num_results, offset)
        return str(result)
>>>>>>> ms/small_fixes
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
