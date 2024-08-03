# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from semantic_kernel.orchestration.sk_context import SKContext
from plugins.bing_connector import BingConnector


class BingPlugin:
    """
    A plugin to search Bing.
    """

    def __init__(self, bing_api_key: str):
        self.bing = BingConnector(api_key=bing_api_key)
        if not bing_api_key or bing_api_key == "...":
            raise Exception("Bing API key is not set")

    @sk_function(
        description="Use Bing to find a page about a topic. The return is a URL of the page found",
        name="find_web_page_about",
        input_description="The topic to search, e.g. 'who won the F1 title in 2023?'",
    )
    @sk_function_context_parameter(
        name="limit", description="How many results to return", default_value="1"
    )
    @sk_function_context_parameter(
        name="offset", description="How many results to skip", default_value="0"
    )
    async def find_web_page_about(self, input: str, context: "SKContext") -> str:
        """
        A native function that uses Bing to find a page URL about a topic.
        """
        result = await self.bing.search_url_async(
            query=input,
            num_results=context.variables.get("limit", 1),
            offset=context.variables.get("offset", 0),
        )
        if result:
            return result[0]
        else:
            return "Nothing found, try again or try to adjust the topic."
