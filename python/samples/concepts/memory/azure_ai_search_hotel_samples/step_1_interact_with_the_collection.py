# Copyright (c) Microsoft. All rights reserved.

import asyncio

from step_0_data_model import HotelSampleClass

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection

###
# The data model used for this sample is based on the hotel data model from the Azure AI Search samples.
# When deploying a new index in Azure AI Search using the import wizard you can choose to deploy the 'hotel-samples'
# dataset, see here: https://learn.microsoft.com/en-us/azure/search/search-get-started-portal.
# This is the dataset used in this sample with some modifications.
# This model adds vectors for the 2 descriptions in English and French.
# Both are based on the 1536 dimensions of the OpenAI models.
# You can adjust this at creation time and then make the change below as well.
# This sample assumes the index is deployed, the vector fields can be empty.
# If the vector fields are empty, change the first_run parameter to True to add the vectors.
###
from semantic_kernel.data import (
    VectorSearchOptions,
)
from semantic_kernel.data.vector_search import add_vector_to_records

first_run = False

# Note: you may need to update this `collection_name` depending upon how your index is named.
COLLECTION_NAME = "hotels-sample-index"


async def add_vectors(collection: AzureAISearchCollection, kernel: Kernel):
    """This is a simple function that uses the add_vector_to_records function to add vectors.

    It first uses the search_client within the collection to get a list of ids.
    and then uses the upsert to add the vectors to the records.
    """
    ids: list[str] = [res.get("hotel_id") async for res in await collection.search_client.search(select="hotel_id")]
    print("sample id:", ids[0])

    hotels = await collection.get_batch(ids)
    if hotels is not None and isinstance(hotels, list):
        for hotel in hotels:
            if not hotel.description_vector or not hotel.description_fr_vector:
                hotel = await add_vector_to_records(kernel, hotel, HotelSampleClass)
                await collection.upsert(hotel)


async def main(query: str, first_run: bool = False):
    # Create the kernel
    kernel = Kernel()
    # Add the OpenAI text embedding service
    embeddings = OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small")
    kernel.add_service(embeddings)
    # Create the Azure AI Search collection
    collection = AzureAISearchCollection[str, HotelSampleClass](
        collection_name=COLLECTION_NAME, data_model_type=HotelSampleClass
    )
    # Check if the collection exists.
    if not await collection.does_collection_exist():
        raise ValueError(
            "Collection does not exist, please create using the "
            "Azure AI Search portal wizard -> Import Data -> Samples -> hotels-sample."
            "During creation adapt the index schema to add the description_vector and description_fr_vector fields."
            "You may need to rename other fields to match the data model."
            "Then run this sample with `first_run=True` to add the vectors."
            "Refer to the README for more information."
        )

    # If it is the first run and there are no vectors, add them.
    if first_run:
        await add_vectors(collection, kernel)

    # Search using just text, by default this will search all the searchable text fields in the index.
    results = await collection.text_search(search_text=query)
    print("Search results using text: ")
    async for result in results.results:
        print(
            f"    {result.record.hotel_id} (in {result.record.address['city']}, "
            f"{result.record.address['country']}): {result.record.description} (score: {result.score})"
        )

    print("\n")

    # Generate the vector for the query
    query_vector = (await embeddings.generate_raw_embeddings([query]))[0]

    print("Search results using vector: ")
    # Use vectorized search to search using the vector.
    results = await collection.vectorized_search(
        vector=query_vector,
        options=VectorSearchOptions(vector_field_name="description_vector"),
    )
    async for result in results.results:
        print(
            f"    {result.record.hotel_id} (in {result.record.address['city']}, "
            f"{result.record.address['country']}): {result.record.description} (score: {result.score})"
        )

    # Delete the collection object so that the connection is closed.
    del collection
    await asyncio.sleep(2)


if __name__ == "__main__":
    query = "swimming pool and good internet connection"
    asyncio.run(main(query=query, first_run=first_run))
