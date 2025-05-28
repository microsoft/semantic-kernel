# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.memory.azure_ai_search_hotel_samples.data_model import (
    HotelSampleClass,
    custom_index,
    load_records,
)
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.connectors.azure_ai_search import AzureAISearchCollection

"""
With the data model and records defined in step_0_data_model.py, this script will create an Azure AI Search collection,
upsert the records, and then search the collection using vector and hybrid search.
The script will print the first five records in the collection and the search results.
The script will also delete the collection at the end.

Note that we add the OpenAITextEmbedding to the collection, which is used to generate the vectors.
To use the built-in embedding in Azure AI Search, remove this and add that definition to the custom_index.
"""


async def main(query: str):
    records = load_records()
    # Create the Azure AI Search collection
    async with AzureAISearchCollection[str, HotelSampleClass](
        record_type=HotelSampleClass, embedding_generator=OpenAITextEmbedding()
    ) as collection:
        # Check if the collection exists.
        if not await collection.does_collection_exist():
            await collection.create_collection(index=custom_index)
        await collection.upsert(records)
        # get the first five records to check the upsert worked.
        results = await collection.get(order_by="HotelName", top=5)
        print("Get first five records: ")
        if results:
            for result in results:
                print(
                    f"    {result.HotelId} (in {result.Address.City}, {result.Address.Country}): {result.Description}"
                )

        print("\n")
        print("Search results using vector: ")
        # Use search to search using the vector.
        results = await collection.search(
            query,
            vector_property_name="DescriptionVector",
        )
        async for result in results.results:
            print(
                f"    {result.record.HotelId} (in {result.record.Address.City}, "
                f"{result.record.Address.Country}): {result.record.Description} (score: {result.score})"
            )
        print("\n")
        print("Search results using hybrid: ")
        # Use hybrid search to search using the vector.
        results = await collection.hybrid_search(
            query,
            vector_property_name="DescriptionVector",
            additional_property_name="Description",
        )
        async for result in results.results:
            print(
                f"    {result.record.HotelId} (in {result.record.Address.City}, "
                f"{result.record.Address.Country}): {result.record.Description} (score: {result.score})"
            )

        await collection.ensure_collection_deleted()


if __name__ == "__main__":
    query = "swimming pool and good internet connection"
    asyncio.run(main(query=query))
