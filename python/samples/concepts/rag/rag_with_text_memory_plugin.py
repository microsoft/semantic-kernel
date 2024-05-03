# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextEmbedding
from semantic_kernel.core_plugins import TextMemoryPlugin
from semantic_kernel.memory import SemanticTextMemory, VolatileMemoryStore
from semantic_kernel.utils.settings import openai_settings_from_dot_env


async def main():
    kernel = Kernel()

    api_key, org_id = openai_settings_from_dot_env()
    service_id = "default"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    )
    embedding_gen = OpenAITextEmbedding(
        service_id="ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
    )

    kernel.add_service(embedding_gen)

    memory = SemanticTextMemory(storage=VolatileMemoryStore(), embeddings_generator=embedding_gen)
    kernel.add_plugin(TextMemoryPlugin(memory), "memory")

    await memory.save_information(collection="generic", id="info1", text="My budget for 2024 is $100,000")

    result = await kernel.invoke_prompt(
        function_name="budget",
        plugin_name="BudgetPlugin",
        prompt="{{memory.recall 'budget by year'}} What is my budget for 2024?",
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
