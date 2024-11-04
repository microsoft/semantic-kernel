# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.search.bing.bing_search import BingSearch


async def main():
    kernel = Kernel()
    service_id = "chat-gpt"
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    connector = BingSearch()
    query = "What is semantic kernel?"
    print("Query: ", query)
    print("\n============================\n")
    results = await connector.search(query, top=2)
    print("String search results: ")
    if results.metadata and results.metadata.get("altered_query", None):
        print(f"  Altered query: {results.metadata['altered_query']}")
    async for result in results.results:
        print(f"    result: {result}")
    print("\n============================\n")
    results = await connector.get_text_search_results(query, top=2)
    print("Text search results: ")
    if results.metadata and results.metadata.get("altered_query", None):
        print(f"  Altered query: {results.metadata['altered_query']}")
    async for result in results.results:
        print(f"    name: {result.name}")
        print(f"    value: {result.value}")
        print(f"    link: {result.link}")
    print("\n============================\n")
    results = await connector.get_search_results(query, top=2)
    print("BingWebPage results: ")
    if results.metadata and results.metadata.get("altered_query", None):
        print(f"  Altered query: {results.metadata['altered_query']}")
    async for result in results.results:
        print(f"    name: {result.name}")
        print(f"    url: {result.url}")
        print(f"    language: {result.language}")
        print(f"    snippet: {result.snippet}")
    print("\n============================\n")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
