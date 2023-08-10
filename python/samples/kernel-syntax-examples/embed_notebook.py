from typing import Tuple
import asyncio
import semantic_kernel as sk
from semantic_kernel.connectors.ai.jina_ai import JinaTextEmbedding
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding

async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the semantic memory
    await kernel.memory.save_information_async(
        "aboutMe", id="info1", text="My name is Andrea"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info2", text="I currently work as a tour guide"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info3", text="I have lived in Seattle"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info4", text="I traveled to France and Italy five times since 2015"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info5", text="My family is from New York"
    )

async def search_memory_examples(kernel: sk.Kernel) -> None:
    questions = [
        "where have I traveled?",
        "where do I live?",
        "what's my name",
        "where's my family from?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await kernel.memory.search_async("aboutMe", question, limit=1, min_relevance_score=0.6)
        print(f"Answer: {result[0].text}\n")

async def main():
    kernel = sk.Kernel()
    api_key, model_id, org_id = sk.jinaai_settings_from_dot_env()
    kernel.add_text_embedding_generation_service(model_id, JinaTextEmbedding(model_id, api_key, org_id))
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())
    kernel.import_skill(sk.core_skills.TextMemorySkill())
    await populate_memory(kernel=kernel)
    await search_memory_examples(kernel=kernel)

if __name__ == "__main__":
    (asyncio.run(main()))