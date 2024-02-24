# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Tuple

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the semantic memory
    await kernel.memory.save_information("aboutMe", id="info1", text="My name is Andrea")
    await kernel.memory.save_information("aboutMe", id="info2", text="I currently work as a tour guide")
    await kernel.memory.save_information("aboutMe", id="info3", text="I've been living in Seattle since 2005")
    await kernel.memory.save_information("aboutMe", id="info4", text="I visited France and Italy five times since 2015")
    await kernel.memory.save_information("aboutMe", id="info5", text="My family is from New York")


async def search_memory_examples(kernel: sk.Kernel) -> None:
    questions = [
        "what's my name",
        "where do I live?",
        "where's my family from?",
        "where have I traveled?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await kernel.memory.search("aboutMe", question)
        print(f"Answer: {result[0].text}\n")


# TODO fix this ASAP
async def setup_chat_with_memory(
    kernel: sk.Kernel,
) -> Tuple[sk.KernelFunction, sk.KernelContext]:
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

    chat_func = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0.8)

    context = kernel.create_new_context()
    context["fact1"] = "what is my name?"
    context["fact2"] = "where do I live?"
    context["fact3"] = "where's my family from?"
    context["fact4"] = "where have I traveled?"
    context["fact5"] = "what do I do for work?"

    context[sk.core_plugins.TextMemoryPlugin.COLLECTION_PARAM] = "aboutMe"
    context[sk.core_plugins.TextMemoryPlugin.RELEVANCE_PARAM] = "0.8"

    context["chat_history"] = ""

    return chat_func, context


async def chat(kernel: sk.Kernel, chat_func: sk.KernelFunction, chat_history: ChatHistory) -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.invoke(chat_func, KernelArguments(user_input=user_input, chat_history=chat_history))
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))

    print(f"ChatBot:> {answer}")
    return True


async def main() -> None:
    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()
    service_id = "chat-gpt"
    kernel.add_service(
        sk_oai.OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
    )
    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
    )
    kernel.add_service(embedding_gen)

    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
    kernel.import_plugin(sk.core_plugins.TextMemoryPlugin(), "TextMemoryPlugin")

    print("Populating memory...")
    await populate_memory(kernel)

    print("Asking questions... (manually)")
    await search_memory_examples(kernel)

    print("Setting up a chat (with memory!)")
    chat_func, context = await setup_chat_with_memory(kernel)

    print("Begin chatting (type 'exit' to exit):\n")
    chatting = True
    while chatting:
        chatting = await chat(kernel, chat_func, context)


if __name__ == "__main__":
    asyncio.run(main())
