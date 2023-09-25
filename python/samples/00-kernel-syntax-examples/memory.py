# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Tuple

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the semantic memory
    await kernel.memory.save_information_async(
        "aboutMe", id="info1", text="My name is Andrea"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info2", text="I currently work as a tour guide"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info3", text="I've been living in Seattle since 2005"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info4", text="I visited France and Italy five times since 2015"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info5", text="My family is from New York"
    )


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
        result = await kernel.memory.search_async("aboutMe", question)
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

    context[sk.core_skills.TextMemorySkill.COLLECTION_PARAM] = "aboutMe"
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

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_chat_service(
        "chat-gpt", sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )
    kernel.add_text_embedding_generation_service(
        "ada", sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id)
    )

    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())
    kernel.import_skill(sk.core_skills.TextMemorySkill())

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
