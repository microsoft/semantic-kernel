# Copyright (c) Microsoft. All rights reserved.


# import pytest


# import semantic_kernel as sk
# import semantic_kernel.connectors.ai.jina_ai as sk_jai


# @pytest.mark.asyncio
# async def test_jina_embeddings_with_memories():
#     kernel = sk.Kernel()


#     # Configure LLM service
#     kernel.add_text_embedding_generation_service(
#         "ViT-B-32::laion2b-s34b-b79k",
#         sk_jai.JinaTextEmbedding("ViT-B-32::laion2b-s34b-b79k"),)
#     kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())


#     # Add some documents to the semantic memory
#     await kernel.memory.save_information_async(
#         "test", id="info1", text="Sharks are fish."
#     )
#     await kernel.memory.save_information_async(
#         "test", id="info2", text="Whales are mammals."
#     )
#     await kernel.memory.save_information_async(
#         "test", id="info3", text="Penguins are birds."
#     )
#     await kernel.memory.save_information_async(
#         "test", id="info4", text="Dolphins are mammals."
#     )
#     await kernel.memory.save_information_async(
#         "test", id="info5", text="Flies are insects."
#     )


#     # Search for documents
#     query = "What are mammals?"
#     result = await kernel.memory.search_async(
#         "test", query, limit=2, min_relevance_score=0.0
#     )
#     print(f"Query: {query}")
#     print(f"\tAnswer 1: {result[0].text}")
#     print(f"\tAnswer 2: {result[1].text}\n")
#     assert "mammals." in result[0].text
#     assert "mammals." in result[1].text


#     query = "What are fish?"
#     result = await kernel.memory.search_async(
#         "test", query, limit=1, min_relevance_score=0.0
#     )
#     print(f"Query: {query}")
#     print(f"\tAnswer: {result[0].text}\n")
#     assert result[0].text == "Sharks are fish."


#     query = "What are insects?"
#     result = await kernel.memory.search_async(
#         "test", query, limit=1, min_relevance_score=0.0
#     )
#     print(f"Query: {query}")
#     print(f"\tAnswer: {result[0].text}\n")
#     assert result[0].text == "Flies are insects."


#     query = "What are birds?"
#     result = await kernel.memory.search_async(
#         "test", query, limit=1, min_relevance_score=0.0
#     )
#     print(f"Query: {query}")
#     print(f"\tAnswer: {result[0].text}\n")
#     assert result[0].text == "Penguins are birds."


# Copyright (c) Microsoft. All rights reserved.


import pytest


import semantic_kernel as sk
import semantic_kernel.connectors.ai.jina_ai as sk_jai


@pytest.mark.asyncio
async def test_jina_embedding_service(create_kernel, get_jai_config):
    kernel = create_kernel
    # api_key, org_id = get_oai_config
    api_key, org_id = get_jai_config
    print(api_key, org_id)

    # kernel = sk.Kernel()
    # api_key, org_id = sk.jinaai_settings_from_dot_env()

    kernel.add_text_embedding_generation_service(
        "ViT-B-32::laion2b-s34b-b79k",
        sk_jai.JinaTextEmbedding("ViT-B-32::laion2b-s34b-b79k", api_key, org_id=org_id),
    )

    # kernel.add_text_embedding_generation_service(
    #     "ViT-B-32::laion2b-s34b-b79k",
    #     sk_jai.JinaTextEmbedding("ViT-B-32::laion2b-s34b-b79k"),)
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())
    # Add some documents to the semantic memory
    await kernel.memory.save_information_async(
        "test", id="info1", text="First do it"
    )
    await kernel.memory.save_information_async(
        "test", id="info2", text="then do it right"
    )

    # # Search for documents
    query = "Who did it?"
    result = await kernel.memory.search_async(
        "test", query, limit=2, min_relevance_score=0.0
    )
    print(f"Query: {query}")
    print(f"\tAnswer 1: {result[0].text}")
    print(f"\tAnswer 2: {result[1].text}\n")
    assert "it" in result[0].text
    assert "it" in result[1].text

    # kernel = create_kernel
    # # api_key, org_id = get_oai_config
    # api_key, org_id = get_jai_config
    # print(api_key, org_id)
    # await kernel.add_text_embedding_generation_service(
    #     "ViT-B-32::laion2b-s34b-b79k",
    #     sk_jai.JinaTextEmbedding("ViT-B-32::laion2b-s34b-b79k", api_key, org_id=org_id),
    # )
    # kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    # await kernel.memory.save_information_async(
    #     "test", id="info1", text="this is a test"
    # )
    # await kernel.memory.save_reference_async(
    #     "test",
    #     external_id="info1",
    #     text="this is a test",
    #     external_source_name="external source",
    # )
