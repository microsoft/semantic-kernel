# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition import sk_function
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
        description="Use Bing to find a page about a topic. The return is a URL of the page found.",
        name="find_web_page_about",
        input_description="Two comma separated values: #1 Offset from the first result (default zero), #2 The topic to search, e.g. '0,who won the F1 title in 2023?'.",
    )
    async def find_web_page_about(self, input: str) -> str:
        """
        A native function that uses Bing to find a page URL about a topic.
        To simplify the integration with Autogen, the input parameter is a string with two comma separated
        values, rather than the usual context dictionary.
        """

        # Input validation, the error message can help self-correct the input
        if "," not in input:
            raise ValueError("The input argument must contain a comma, e.g. '0,who won the F1 title in 2023?'")

        parts = input.split(",", 1)
        result = await self.bing.search_url_async(query=parts[1], num_results=1, offset=parts[0])
        if result:
            return result[0]
        else:
            return f"Nothing found, try again or try to adjust the topic."
