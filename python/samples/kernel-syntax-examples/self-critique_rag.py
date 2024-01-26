# Copyright (c) Microsoft. All rights reserved.

import asyncio

from dotenv import dotenv_values

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextCompletion,
    AzureTextEmbedding,
)
from semantic_kernel.connectors.memory.azure_cognitive_search import (
    AzureCognitiveSearchMemoryStore,
)
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.orchestration.context_variables import ContextVariables

COLLECTION_NAME = "generic"


async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the ACS semantic memory
    await kernel.memory.save_information(COLLECTION_NAME, id="info1", text="My name is Andrea")
    await kernel.memory.save_information(COLLECTION_NAME, id="info2", text="I currently work as a tour guide")
    await kernel.memory.save_information(COLLECTION_NAME, id="info3", text="I've been living in Seattle since 2005")
    await kernel.memory.save_information(
        COLLECTION_NAME,
        id="info4",
        text="I visited France and Italy five times since 2015",
    )
    await kernel.memory.save_information(COLLECTION_NAME, id="info5", text="My family is from New York")


async def main() -> None:
    kernel = sk.Kernel()
    tms = TextMemoryPlugin()
    kernel.import_plugin(tms, "memory")

    config = dotenv_values(".env")

    AZURE_COGNITIVE_SEARCH_ENDPOINT = config["AZURE_COGNITIVE_SEARCH_ENDPOINT"]
    AZURE_COGNITIVE_SEARCH_ADMIN_KEY = config["AZURE_COGNITIVE_SEARCH_ADMIN_KEY"]
    AZURE_OPENAI_API_KEY = config["AZURE_OPENAI_API_KEY"]
    AZURE_OPENAI_ENDPOINT = config["AZURE_OPENAI_ENDPOINT"]
    vector_size = 1536

    # Setting up OpenAI services for text completion and text embedding
    kernel.add_text_completion_service(
        "dv",
        AzureTextCompletion(
            deployment_name="gpt-35-turbo-instruct",
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        ),
    )
    kernel.add_text_embedding_generation_service(
        "ada",
        AzureTextEmbedding(
            deployment_name="text-embedding-ada-002",
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        ),
    )

    connector = AzureCognitiveSearchMemoryStore(
        vector_size, AZURE_COGNITIVE_SEARCH_ENDPOINT, AZURE_COGNITIVE_SEARCH_ADMIN_KEY
    )

    # Register the memory store with the kernel
    kernel.register_memory_store(memory_store=connector)

    print("Populating memory...")
    await populate_memory(kernel)

    sk_prompt_rag = """
Assistant can have a conversation with you about any topic.
It can give explicit instructions or say 'I don't know' if
it does not have an answer.

Here is some background information about the user that you should use to answer the question below:
{{ memory.recall $user_input }}
User: {{$user_input}}
Assistant: """.strip()
    sk_prompt_rag_sc = """
You will get a question, background information to be used with that question and a answer that was given. 
You have to answer Grounded or Ungrounded or Unclear.
Grounded if the answer is based on the background information and clearly answers the question.
Ungrounded if the answer could be true but is not based on the background information.
Unclear if the answer does not answer the question at all.
Question: {{$user_input}}
Background: {{ memory.recall $user_input }}
Answer: {{ $input }}
Remember, just answer Grounded or Ungrounded or Unclear: """.strip()

    user_input = "Do I live in New York City?"
    print(f"Question: {user_input}")
    chat_func = kernel.create_semantic_function(sk_prompt_rag, max_tokens=1000, temperature=0.5)
    self_critique_func = kernel.create_semantic_function(sk_prompt_rag_sc, max_tokens=4, temperature=0.0)

    answer = await kernel.run(
        chat_func,
        input_vars=ContextVariables(
            variables={
                "user_input": user_input,
                "collection": COLLECTION_NAME,
                "limit": "2",
            }
        ),
    )
    print(f"Answer: {str(answer).strip()}")
    check = await kernel.run(self_critique_func, input_context=answer)
    print(f"The answer was {str(check).strip()}")

    print("-" * 50)
    print("   Let's pretend the answer was wrong...")
    answer.variables.variables["input"] = "Yes, you live in New York City."
    print(f"Answer: {str(answer).strip()}")
    check = await kernel.run(self_critique_func, input_context=answer)
    print(f"The answer was {str(check).strip()}")

    print("-" * 50)
    print("   Let's pretend the answer is not related...")
    answer.variables.variables["input"] = "Yes, the earth is not flat."
    print(f"Answer: {str(answer).strip()}")
    check = await kernel.run(self_critique_func, input_context=answer)
    print(f"The answer was {str(check).strip()}")

    await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
