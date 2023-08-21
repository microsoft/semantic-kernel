# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Tuple

import semantic_kernel as sk
from semantic_kernel.connectors.memory.azure_cognitive_search import (
    AzureCognitiveSearchMemoryStore,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextCompletion,
    AzureTextEmbedding,
)


COLLECTION_NAME = "acs-index-sample"


async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the ACS semantic memory
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info1", text="My name is Andrea"
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info2", text="I currently work as a tour guide"
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info3", text="I've been living in Seattle since 2005"
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME,
        id="info4",
        text="I visited France and Italy five times since 2015",
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info5", text="My family is from New York"
    )


async def search_acs_memory_questions(kernel: sk.Kernel) -> None:
    questions = [
        "what's my name",
        "where do I live?",
        "where's my family from?",
        "where have I traveled?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await kernel.memory.search_async(COLLECTION_NAME, question)
        print(f"Answer: {result[0].text}\n")


async def setup_chat_with_memory(
    kernel: sk.Kernel,
) -> Tuple[sk.SKFunctionBase, sk.SKContext]:
    sk_prompt = """
    ChatBot can have a conversation with you about any topic.
    It can give explicit instructions or say 'I don't know' if
    it does not have an answer.

    Information about me, from previous conversations:
    - {{$fact1}} {{recall $fact1}}
    - {{$fact2}} {{recall $fact2}}
    - {{$fact3}} {{recall $fact3}}
    - {{$fact4}} {{recall $fact4}}
    - {{$fact5}} {{recall $fact5}}

    Chat:
    {{$chat_history}}
    User: {{$user_input}}
    ChatBot: """.strip()

    chat_func = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0.8
    )

    context = kernel.create_new_context()
    context["fact1"] = "what is my name?"
    context["fact2"] = "where do I live?"
    context["fact3"] = "where's my family from?"
    context["fact4"] = "where have I traveled?"
    context["fact5"] = "what do I do for work?"

    context[sk.core_skills.TextMemorySkill.COLLECTION_PARAM] = COLLECTION_NAME
    context[sk.core_skills.TextMemorySkill.RELEVANCE_PARAM] = 0.8

    context["chat_history"] = ""

    return chat_func, context


async def chat(
    kernel: sk.Kernel, chat_func: sk.SKFunctionBase, context: sk.SKContext
) -> bool:
    try:
        user_input = input("User:> ")
        context["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.run_async(chat_func, input_vars=context.variables)
    context["chat_history"] += f"\nUser:> {user_input}\nChatBot:> {answer}\n"

    print(f"ChatBot:> {answer}")
    return True


async def main() -> None:
    kernel = sk.Kernel()

    # Add OpenAI services
    (
        open_ai_deployment,
        open_api_key,
        open_ai_endpoint,
    ) = sk.azure_openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        "dv",
        AzureTextCompletion(
            deployment_name=open_ai_deployment,
            endpoint=open_ai_endpoint,
            api_key=open_api_key,
        ),
    )
    kernel.add_text_embedding_generation_service(
        "ada",
        AzureTextEmbedding(
            deployment_name=open_ai_deployment,
            endpoint=open_ai_endpoint,
            api_key=open_api_key,
        ),
    )

    ACS_ENDPOINT = os.environ["AZURE_ACS_ENDPOINT"]
    ACS_ADMIN_KEY = os.environ["AZURE_ACS_ADMIN_KEY"]
    vector_size = 1536

    connector = AzureCognitiveSearchMemoryStore(
        vector_size, ACS_ENDPOINT, ACS_ADMIN_KEY
    )

    kernel.register_memory_store(memory_store=connector)
    kernel.import_skill(sk.core_skills.TextMemorySkill())

    print("Populating memory...")
    await populate_memory(kernel)

    print("Asking questions... (manually)")
    await search_acs_memory_questions(kernel)


if __name__ == "__main__":
    asyncio.run(main())