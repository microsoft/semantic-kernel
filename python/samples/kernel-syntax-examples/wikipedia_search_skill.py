# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion
from semantic_kernel.connectors.search_engine import WikipediaConnector
from semantic_kernel.core_skills import WebSearchEngineSkill

kernel = sk.Kernel()
api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_text_completion_service(
    "dv", OpenAITextCompletion("text-davinci-003", api_key, org_id)
)
wiki_connector = WikipediaConnector()
web_skill = kernel.import_skill(WebSearchEngineSkill(wiki_connector), "WebSearch")


async def simple_search():
    # Returns a list of tuples that contain the title and a small snippet from a relevent Wikipedia article to the query
    prompt = "Where is the Golden Gate Bridge?"
    search_async = web_skill["searchAsync"]
    result = await search_async.invoke_async(prompt)
    print(result)

    # Will attempt to remedy typos or unclear queries
    prompt = "pyfth0n profgaming"
    search_async = web_skill["searchAsync"]
    result = await search_async.invoke_async(prompt)
    print(result)


async def semantic_function():
    # Combine with a semantic function to get output generated from data found on Wikipedia
    prompt = """
    Answer the question using only the data that is provided in the data section.
    Do not use any prior knowledge to answer the question.
    Cite sources with links in a numbered list after the answer.

    Data: {{WebSearch.SearchAsync "Machine learning"}}
    Question: "What is machine learning and what are its applications?"
    Answer:
    """

    qna = kernel.create_semantic_function(prompt, temperature=0.2)
    context = kernel.create_new_context()
    context["num_results"] = "5"
    context["offset"] = "0"
    result = await qna.invoke_async(context=context)
    print(result)

    """
    Output:

    Machine learning is an umbrella term for solving problems for which development of algorithms by human programmers 
    would be cost-prohibitive. Its applications include unsupervised learning, which analyzes a stream of data and 
    finds patterns and makes predictions, and quantum machine learning, which integrates quantum algorithms within 
    machine learning programs. Additionally, machine learning-based attention is a mechanism, mimicking cognitive 
    attention, which calculates "soft" weights for each word, more precisely for its embedding. The most common use 
    of the term refers to machine learning models such as the Transformer, which is a deep learning architecture 
    that relies on the parallel multi-head attention mechanism.

    Sources:
    1. https://en.wikipedia.org/wiki/Machine_learning
    2. https://en.wikipedia.org/wiki/Quantum_machine_learning
    3. https://en.wikipedia.org/wiki/Attention_(machine_learning)
    4. https://en.wikipedia.org/wiki/Transformer_(machine_learning_model)
    5. https://en.wikipedia.org/wiki/Artificial_intelligence
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(simple_search())
    asyncio.run(semantic_function())  # Note: beware of high token usage
