import os

from dotenv import load_dotenv

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_plugins import WebSearchEnginePlugin

load_dotenv()


async def main():
    kernel = sk.Kernel()
    deployment, key, endpoint, api_version = sk.azure_openai_settings_from_dot_env(include_api_version=True)
    kernel.add_chat_service(
        "chat-gpt",
        AzureChatCompletion(
            deployment_name=deployment,
            api_key=key,
            endpoint=endpoint,
            api_version=api_version,
        ),
    )
    connector = BingConnector(api_key=os.getenv("BING_API_KEY"))
    web_plugin = kernel.import_plugin(WebSearchEnginePlugin(connector), "WebSearch")

    prompt = "Who is Leonardo DiCaprio's current girlfriend?"
    search = web_plugin["searchAsync"]
    result = await search.invoke(prompt)
    print(result)

    """
    Output:
    ["Celebrity Celebrity News Everything You Need to Know About Leonardo DiCaprio and Camila Morrone's
    Relationship From the beginning of their romance to today, we track their relationship here. By..."]
    """

    prompt = """
    Answer the question using only the data that is provided in the data section.
    Do not use any prior knowledge to answer the question.
    Data: {{WebSearch.SearchAsync "What is semantic kernel?"}}
    Question: What is semantic kernel?
    Answer:
    """

    qna = kernel.create_semantic_function(prompt, temperature=0.2)
    context = kernel.create_new_context()
    context["num_results"] = "10"
    context["offset"] = "0"
    result = await qna.invoke(context=context)
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
