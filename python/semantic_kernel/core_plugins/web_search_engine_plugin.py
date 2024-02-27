import sys
from typing import TYPE_CHECKING, Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function

if TYPE_CHECKING:
    from semantic_kernel.connectors.search_engine.connector import ConnectorBase


class WebSearchEnginePlugin:
    """
    Description: A plugin that provides web search engine functionality

    Usage:
        connector = BingConnector(bing_search_api_key)
        kernel.import_plugin_from_object(WebSearchEnginePlugin(connector), plugin_name="WebSearch")

    Examples:
        {{WebSearch.SearchAsync "What is semantic kernel?"}}
        =>  Returns the first `num_results` number of results for the given search query
            and ignores the first `offset` number of results
            (num_results and offset are specified in KernelContext)
    """

    _connector: "ConnectorBase"

    def __init__(self, connector: "ConnectorBase") -> None:
        self._connector = connector

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
