import asyncio

from semantic_kernel.connectors.memory.astradb.ai_sample.utils import kernel, COLLECTION_NAME


def openai_search():
    question = "As a friendly AI Copilot, answer the question: Did Albert Einstein like coffee?"
    prompt = kernel.create_semantic_function(question)
    print(f"Question: {question}\nAnswer: {prompt()}")


async def memory_search():
    question = "What happens if there a role has access to the keyspace/table level and I grant row access?"
    result = await kernel.memory.search_async(COLLECTION_NAME, question)
    print(f"Question: {question}")
    print(f"Retrieved document: {result[0].text}, {result[0].relevance}")

asyncio.run(memory_search())
