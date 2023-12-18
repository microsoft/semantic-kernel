import asyncio

from semantic_kernel.connectors.memory.astradb.ai_sample.utils import kernel, COLLECTION_NAME


def openai_search():
    while True:
        question = input("Question (type 'exit' to quit): ")
        if question.lower() == 'exit':
            print("Thanks!")
            break

        prompt = kernel.create_semantic_function(question)
        print(f"Answer: {prompt()}")


async def memory_search():
    while True:
        question = input("Question (type 'exit' to quit): ")
        if question.lower() == 'exit':
            print("Thanks!")
            break

        result = await kernel.memory.search_async(COLLECTION_NAME, question)
        print(f"Retrieved document: {result[0].text}, {result[0].relevance}")

asyncio.run(memory_search())
