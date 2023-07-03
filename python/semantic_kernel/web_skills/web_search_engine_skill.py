from semantic_kernel.web_skills.connectors import Connector
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter


class WebSearchEngineSkill:
    """
    Description: A skill that provides web search engine functionality

    Usage:
        connector = BingConnector(bing_search_api_key)
        kernel.import_skill(WebSearchEngineSkill(connector), skill_name="WebSearch")

    Examples:
        {{WebSearch.SearchAsync "What is semantic kernel?"}}         => Returns the first `count` number of results for the given search query and ignores the first `offset` number of results (count and offset are specified in SKContext)
    """

    _connector: Connector

    def __init__(self, connector: Connector) -> None:
        self._connector = connector

    @sk_function(
        description="Performs a web search for a given query", name="searchAsync"
    )
    @sk_function_context_parameter(
        name="count",
        description="The number of search results to return",
        default_value="1",
    )
    @sk_function_context_parameter(
        name="offset",
        description="The number of search results to skip",
        default_value="0",
    )
    async def search_async(self, query: str, context: SKContext) -> str:
        """
        Returns the search results of the query provided.
        Returns `count` results and ignores the first `offset`.

        :param query: search query
        :param context: contains the context of count and offset parameters
        :return: stringified list of search results
        """

        _, _count = context.variables.get("count")
        _, _offset = context.variables.get("offset")
        result = await self._connector.search_async(query, _count, _offset)
        return str(result)
