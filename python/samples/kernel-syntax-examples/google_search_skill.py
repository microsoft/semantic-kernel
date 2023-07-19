import os

from dotenv import load_dotenv

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion
from semantic_kernel.connectors.search_engine import GoogleConnector
from semantic_kernel.core_skills import WebSearchEngineSkill

load_dotenv()


async def main():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        "dv", OpenAITextCompletion("text-davinci-003", api_key, org_id)
    )

    """
    Instantiate a Google Connector
    Make sure to have the following keys in a .env file or set as environment variables
    - GOOGLE_API_KEY
    - GOOGLE_SEARCH_ENGINE_ID
    """
    connector = GoogleConnector(
        api_key=os.getenv("GOOGLE_API_KEY"),
        search_engine_id=os.getenv("GOOGLE_SEARCH_ENGINE_ID"),
    )

    # Import the WebSearchEngineSkill and pass the Google Connector to it.
    web_skill = kernel.import_skill(WebSearchEngineSkill(connector), "WebSearch")

    # The search query
    prompt = "Who is Leonardo DiCaprio's current girlfriend?"
    search_async = web_skill["searchAsync"]

    # By default, only one search result is provided
    result = await search_async.invoke_async(prompt)
    print(result)

    """
    Output:
    ["Celebrity Celebrity News Everything You Need to Know About Leonardo DiCaprio and Camila Morrone's
    Relationship From the beginning of their romance to today, we track their relationship here. By..."]
    """

    # Following example demonstrates the use of the skill within a semantic function
    prompt = """
    Answer the question using only the data that is provided in the data section.
    Do not use any prior knowledge to answer the question.
    Data: {{WebSearch.SearchAsync "What is semantic kernel?"}}
    Question: What is semantic kernel?
    Answer:
    """

    qna = kernel.create_semantic_function(prompt, temperature=0.2)
    context = kernel.create_new_context()

    """
    Two context parameters can be passed to the search engine skill.
    - num_results controls the number of results returned by the web search.
    - offset controls the number of results to omit.
    """
    context["num_results"] = "10"
    context["offset"] = "0"

    result = await qna.invoke_async(context=context)
    print(result)

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
