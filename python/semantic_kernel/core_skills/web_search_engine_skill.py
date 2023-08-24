import typing as t

from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

if t.TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


class WebSearchEngineSkill:
    """
    Description: A skill that provides web search engine functionality

    Usage:
        connector = BingConnector(bing_search_api_key)
        kernel.import_skill(WebSearchEngineSkill(connector), skill_name="WebSearch")

    Examples:
        {{WebSearch.SearchAsync "What is semantic kernel?"}}
        =>  Returns the first `num_results` number of results for the given search query
            and ignores the first `offset` number of results
            (num_results and offset are specified in SKContext)
    """

    _connector: "ConnectorBase"

    def __init__(self, connector: "ConnectorBase") -> None:
        self._connector = connector

    @sk_function(
        description="Performs a web search for a given query", name="searchAsync"
    )
    @sk_function_context_parameter(
        name="num_results",
        description="The number of search results to return",
        default_value="1",
    )
    @sk_function_context_parameter(
        name="offset",
        description="The number of search results to skip",
        default_value="0",
    )
    async def search_async(self, query: str, context: "SKContext") -> str:
        """
        Returns the search results of the query provided.
        Returns `num_results` results and ignores the first `offset`.

        :param query: search query
        :param context: contains the context of count and offset parameters
        :return: stringified list of search results
        """

        _, _num_results = context.variables.get("num_results")
        _, _offset = context.variables.get("offset")
        result = await self._connector.search_async(query, _num_results, _offset)
        return str(result)
