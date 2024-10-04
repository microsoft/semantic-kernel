# Copyright (c) Microsoft. All rights reserved.
import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory


async def main():
    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()
    service_id = "default"
    kernel.add_service(
        sk_oai.OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    )
    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
    )
    kernel.add_service(embedding_gen)

    memory = SemanticTextMemory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
    kernel.import_plugin_from_object(sk.core_plugins.TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(collection="generic", id="info1", text="My budget for 2024 is $100,000")

    result = await kernel.invoke_prompt(
        function_name="budget",
        plugin_name="BudgetPlugin",
        prompt="{{recall 'budget by year'}} What is my budget for 2024?",
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
