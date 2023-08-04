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

context = kernel.create_new_context()
context["num_results"] = "10"
context["offset"] = "0"

search_async = web_skill["searchAsync"]


async def simple_search():
    # Returns a list of tuples that contain the title and a small snippet from a relevent Wikipedia article to the query
    prompt = "Where is the Golden Gate Bridge?"
    result = await search_async.invoke_async(prompt)
    print(result)

    prompt = "One small step for man..."
    result = await search_async.invoke_async(prompt)
    print(result)

    # Will attempt to remedy typos or unclear queries
    prompt = "pyfth0n profgaming"
    result = await search_async.invoke_async(prompt)
    print(result)

    """
    Output:

    Where is the Golden Gate Bridge?
    [('Golden Gate Bridge', 'The Golden Gate Bridge is a suspension bridge spanning the Golden Gate, the 
    one-mile-wide (1.6\xa0km) strait connecting San Francisco Bay and the Pacific')]

    One small step for man...
    [('Neil Armstrong', " When Armstrong first stepped onto the lunar surface, he famously said: &quot;That's 
    one small step for [a] man, one giant leap for mankind.&quot; It was broadcast")]

    pyfth0n profgaming
    [('Python (programming language)', 'Python is a high-level, general-purpose programming language. Its design 
    philosophy emphasizes code readability with the use of significant indentation')]

    """


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


async def get_updated_info():
    prompt = """
    Answer the question using only the data that is provided in the data section.
    Favor information that is more recent and discard outdated information.
    Do not use any other information sources.
    Cite sources with links in a labeled and numbered list after the answer.

    Data: {{WebSearch.SearchAsync "NBA champion"}}
    Question: "Who won the NBA?"
    Answer:
    """

    qna = kernel.create_semantic_function(prompt, temperature=0.2)
    result = await qna.invoke_async(context=context)
    print(result)

    """
    Output:

    The National Basketball Association (NBA) champion for the most recent season is the Denver Nuggets, 
    who won the 2023 NBA Finals. 

    Sources: 
    1. https://en.wikipedia.org/wiki/List_of_NBA_champions
    2. https://en.wikipedia.org/wiki/National_Basketball_Association
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(simple_search())

    # Note: beware of high token usage
    asyncio.run(semantic_function())
    asyncio.run(get_updated_info())
