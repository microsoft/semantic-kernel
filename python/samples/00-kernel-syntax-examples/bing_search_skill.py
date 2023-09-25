import os

from dotenv import load_dotenv

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_skills import WebSearchEngineSkill

load_dotenv()


async def main():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_chat_service(
        "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )
    connector = BingConnector(api_key=os.getenv("BING_API_KEY"))
    web_skill = kernel.import_skill(WebSearchEngineSkill(connector), "WebSearch")

    prompt = "Who is Leonardo DiCaprio's current girlfriend?"
    search_async = web_skill["searchAsync"]
    result = await search_async.invoke_async(prompt)
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
