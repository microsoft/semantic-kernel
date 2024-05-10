# Copyright (c) Microsoft. All rights reserved.

import os

from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.search_engine import GoogleConnector
from semantic_kernel.core_plugins import WebSearchEnginePlugin
from semantic_kernel.functions import KernelArguments

load_dotenv()


async def main():
    kernel = Kernel()
    kernel.add_service(
        OpenAIChatCompletion(service_id="chat-gpt", ai_model_id="gpt-3.5-turbo")
    )

    """
    Instantiate a Google Connector
    Make sure to have the following keys in a .env file or set as environment variables
    - GOOGLE_API_KEY
    - GOOGLE_SEARCH_ENGINE_ID

    A Google Custom Search API has to be created in order to have an API key and a search engine ID.
    To create a Google Custom Search API, follow the guide - https://developers.google.com/custom-search/v1/overview.
    If you have already created the service, the credentials can be found in the Credentials tab on the page
    https://console.cloud.google.com/apis/api/customsearch.googleapis.com
    """
    connector = GoogleConnector(
        api_key=os.getenv("GOOGLE_API_KEY"),
        search_engine_id=os.getenv("GOOGLE_SEARCH_ENGINE_ID"),
    )

    # Import the WebSearchEnginePlugin and pass the Google Connector to it.
    web_plugin = kernel.add_plugin(WebSearchEnginePlugin(connector), "WebSearch")

    # The search query
    search = web_plugin["searchAsync"]
    prompt = "Who is Leonardo DiCaprio's current girlfriend?"

    # By default, only one search result is provided
    result = await search.invoke(kernel, query=prompt)
    print(str(result))

    """
    Output:
    ["Celebrity Celebrity News Everything You Need to Know About Leonardo DiCaprio and Camila Morrone's
    Relationship From the beginning of their romance to today, we track their relationship here. By..."]
    """

    # Following example demonstrates the use of the plugin within a semantic function
    prompt = """
    Answer the question using only the data that is provided in the data section.
    Do not use any prior knowledge to answer the question.
    Data: {{WebSearch.SearchAsync "What is semantic kernel?"}}
    Question: What is semantic kernel?
    Answer:
    """

    qna = kernel.add_function(
        plugin_name="qa",
        function_name="qna",
        prompt=prompt,
        prompt_execution_settings=PromptExecutionSettings(temperature=0.2),
    )

    """
    Two context parameters can be passed to the search engine plugin.
    - num_results controls the number of results returned by the web search.
    - offset controls the number of results to omit.
    """
    arguments = KernelArguments(num_results="10", offset="0")

    result = await qna.invoke(kernel, arguments)
    print(str(result))

    """
    Output:
    Semantic Kernel is an open-source SDK that lets you easily combine AI services like OpenAI,
    Azure OpenAI, and Hugging Face with conventional programming languages like C# and Python.
    By doing so, you can create AI apps that combine the best of both worlds.
    Semantic Kernel is at the center of the copilot stack.
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
