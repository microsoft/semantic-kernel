# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIEmbeddingPromptExecutionSettings, OpenAITextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.data import (
    VectorSearchFilter,
    VectorSearchOptions,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordUtils,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)


@vectorstoremodel
class HotelSampleClass(BaseModel):
    hotel_id: Annotated[str, VectorStoreRecordKeyField]
    hotel_name: Annotated[str | None, VectorStoreRecordDataField()] = None
    description: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="description_vector")
    ]
    description_vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            dimensions=1536,
            local_embedding=True,
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
        ),
    ] = None
    description_fr: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="description_fr_vector")
    ]
    description_fr_vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            dimensions=1536,
            local_embedding=True,
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
        ),
    ] = None
    category: Annotated[str, VectorStoreRecordDataField()]
    tags: Annotated[list[str], VectorStoreRecordDataField()]
    parking_included: Annotated[bool | None, VectorStoreRecordDataField()] = None
    last_renovation_date: Annotated[str | None, VectorStoreRecordDataField()] = None
    rating: Annotated[float, VectorStoreRecordDataField()]
    location: Annotated[dict[str, Any], VectorStoreRecordDataField()]
    address: Annotated[dict[str, str | None], VectorStoreRecordDataField()]
    rooms: Annotated[list[dict[str, Any]], VectorStoreRecordDataField()]


HotelSampleClassType = TypeVar("HotelSampleClassType", bound=HotelSampleClass)


async def add_vectors(store, vectorizer):
    ids: list[str] = [res.get("hotel_id") async for res in await store.search_client.search(select="hotel_id")]
    print("sample id:", ids[0])

    hotels = await store.get_batch(ids)
    if hotels is not None and isinstance(hotels, list):
        for hotel in hotels:
            if not hotel.description_vector or not hotel.description_fr_vector:
                hotel = await vectorizer.add_vector_to_records(hotel, HotelSampleClass)
                await store.upsert(hotel)


async def main(first_run: bool = False):
    kernel = Kernel()
    embeddings = OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small")
    kernel.add_service(embeddings)
    vectorizer = VectorStoreRecordUtils(kernel)
    store = AzureAISearchCollection[HotelSampleClassType](
        collection_name="hotels-sample-index", data_model_type=HotelSampleClass
    )
    if not await store.does_collection_exist():
        raise ValueError(
            "Collection does not exist, please create using the "
            "Azure AI Search portal wizard -> Import Data -> Samples -> hotels-sample."
            "During creation adopt the schema to add the description_vector and description_fr_vector fields."
            "Then run this sample with `first_run=True` to add the vectors."
        )

    if first_run:
        await add_vectors(store, vectorizer)

    query = "swimming pool and good internet connection"
    query_vector = (await embeddings.generate_raw_embeddings([query]))[0]

    results = await store.search(query_type="vectorizable_text_search_query", query=query)
    print("Search results using text: ")
    for result in results:
        print(
            f"    {result.record.hotel_id} (in {result.record.address['city']}, "
            f"{result.record.address['country']}): {result.record.description} (score: {result.score})"
        )

    print("\n")

    print("Search results using vector: ")
    results = await store.search(
        query_type="vectorized_search_query",
        vector=query_vector,
        search_options=VectorSearchOptions(vector_field_name="description_vector"),
    )
    for result in results:
        print(
            f"    {result.record.hotel_id} (in {result.record.address['city']}, "
            f"{result.record.address['country']}): {result.record.description} (score: {result.score})"
        )

    print("\n")

    print("Search results using hybrid text and vector: ")
    results = await store.search(
        query_type="hybrid_text_vectorized_search_query",
        query=query,
        vector=query_vector,
        search_options=VectorSearchOptions(vector_field_name="description_vector"),
    )
    for result in results:
        print(
            f"    {result.record.hotel_id} (in {result.record.address['city']}, "
            f"{result.record.address['country']}): {result.record.description} (score: {result.score})"
        )

    print("\n")

    print("Search results using hybrid text and vector with filter: ")
    results = await store.search(
        query_type="hybrid_text_vectorized_search_query",
        query=query,
        vector=query_vector,
        search_options=VectorSearchOptions(
            vector_field_name="description_vector",
            filter=VectorSearchFilter.any_tag_equal_to(
                field_name="tags",
                value="free wifi",
            ).equal_to(field_name="category", value="Luxury"),
        ),
    )
    for result in results:
        print(
            f"    {result.record.hotel_id} (in {result.record.address['city']}, "
            f"{result.record.address['country']}): {result.record.description} (score: {result.score})"
        )

    del store
    await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
