# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion
from semantic_kernel.connectors.search_engine import WikipediaConnector
from semantic_kernel.core_skills import WebSearchEngineSkill


async def main():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        "dv", OpenAITextCompletion("text-davinci-003", api_key, org_id)
    )
    connector = WikipediaConnector()
    web_skill = kernel.import_skill(WebSearchEngineSkill(connector), "WebSearch")

    
    # Returns a list of tuples that contain the title and a small snippet from a relevent Wikipedia article to the query
    prompt = "Where is the Golden Gate Bridge?"
    search_async = web_skill["searchAsync"]
    result = await search_async.invoke_async(prompt)
    print(result)

    # Will attempt to remedy typos or unclear queries
    prompt = "pyfth0n profgaming lang"
    search_async = web_skill["searchAsync"]
    result = await search_async.invoke_async(prompt)
    print(result)

    # Combine with a semantic function to get output generated from data found on Wikipedia
    prompt = """
    Answer the question using only the data that is provided in the data section.
    Do not use any prior knowledge to answer the question.
    Data: {{WebSearch.SearchAsync "What is machine learning?"}}
    Question: "Explain specific applications of machine learning."
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
    Machine learning has a wide range of applications, including but not limited to: Adversarial machine learning, 
    which is the study of attacks on machine learning algorithms and defenses against such attacks; Quantum machine 
    learning, which is the integration of quantum algorithms within machine learning programs; Active learning, which 
    is a special case of machine learning in which a learning algorithm can interactively query a user or other 
    information source; Support vector machines, which are supervised learning models with associated learning algorithms; 
    and Boosting, which is an ensemble meta-algorithm for reducing bias and variance in supervised learning.
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
