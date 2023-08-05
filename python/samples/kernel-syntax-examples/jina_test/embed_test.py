

# import semantic_kernel as sk
# import semantic_kernel.connectors.ai.jina_ai as sk_jai
# kernel = sk.Kernel()

#     # Configure LLM service
# kernel.add_text_embedding_generation_service(
#     "ViT-B-32::laion2b-s34b-b79k",
#     sk_jai.JinaTextEmbedding("ViT-B-32::laion2b-s34b-b79k"),)

# text=['First do it',
# 'then do it right',
# 'then do it better',]
# # @async
# embed= kernel.generate_embeddings_async(text)
      
# print(embed)
# install the inference_client using pip:
# pip install -U inference_client
# from inference_client import Client
# import semantic_kernel as sk
import semantic_kernel.connectors.ai.jina_ai as sk_jai
# # import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf
import asyncio

# # print("*******\n")
# # from dotenv import dotenv_values
# # c=(dotenv_values(".env"))
# # for k, v in c.items():
# #     print(k,v)
# # print("*******\n")
# # async def main() -> None:
# #     kernel = sk.Kernel()
# #     api_key, org_id = sk.openai_settings_from_dot_env()

# async def main2():
#     print("Start")
#     kernel = sk.Kernel()

#     # Configure LLM service
#     kernel.add_text_embedding_generation_service(
#         "sentence-transformers/all-MiniLM-L6-v2",
#         sk_hf.HuggingFaceTextEmbedding("sentence-transformers/all-MiniLM-L6-v2"),
#     )
#     kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

# # Add some documents to the semantic memory
#     await kernel.memory.save_information_async(
#         "test", id="info1", text="Sharks are fish."
#     )
#     await kernel.memory.save_information_async(
#         "test", id="info2", text="Whales are mammals."
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

# if __name__ == "__main2__":
#     print(asyncio.run(main2()))
    
#     print("End")





async def main():
    kernel = sk.Kernel()

    api_key, org_id = sk.jinaai_settings_from_dot_env()
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

if __name__ == "__main__":
    print(asyncio.run(main()))
    
    print("End")
