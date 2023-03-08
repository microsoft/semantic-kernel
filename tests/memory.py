# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
from semantic_kernel.core_skills import TextMemorySkill


def build_kernel() -> sk.KernelBase:
    kernel = (
        sk.kernel_builder().with_memory_storage(sk.memory.VolatileMemoryStore()).build()
    )

    # Setup kernel with OpenAI completion and embedding backends
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.config.add_openai_completion_backend(
        "davinci-003", "text-davinci-003", api_key, org_id
    )
    kernel.config.add_open_ai_embeddings_backend(
        "ada-002", "text-embedding-ada-002", api_key, org_id
    )

    return kernel


async def populate_memory(kernel: sk.KernelBase) -> None:
    # Add some documents to the kernel's memory
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
        "aboutMe", id="info4", text="I visited Francy and Italy five times since 2015"
    )
    await kernel.memory.save_information_async(
        "aboutMe", id="info5", text="My family is from New York"
    )


async def search_memory_examples(kernel: sk.KernelBase) -> None:
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


async def setup_chat_with_memory(kernel: sk.KernelBase) -> None:
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
    {{$history}}
    User: {{$userInput}}
    ChatBot: """.strip()

    chat_func = sk.extensions.create_semantic_function(
        kernel, sk_prompt, max_tokens=200, temperature=0.8
    )

    context = kernel.create_new_context()
    context["fact1"] = "My name is Andrea"
    context["fact2"] = "I currently work as a tour guide"
    context["fact3"] = "I've been living in Seattle since 2005"
    context["fact4"] = "I visited Francy and Italy five times since 2015"
    context["fact5"] = "My family is from New York"

    context[TextMemorySkill.COLLECTION_PARAM] = "aboutMe"
    context[TextMemorySkill.RELEVANCE_PARAM] = 0.8

    context["chat_history"] = ""

    return chat_func, context


async def chat(
    kernel: sk.KernelBase, chat_func: sk.SKFunctionBase, context: sk.ContextVariables
) -> None:
    try:
        human_input = input("Human:>")
        context["human_input"] = human_input
    except KeyboardInterrupt:
        print("Exiting chat...")
        return

    if human_input == "exit":
        print("Exiting chat...")
        return

    answer = await kernel.run_on_vars_async(context, chat_func)
    context["chat_history"] += f"\nHuman:>{human_input}\nChatBot:>{answer}\n"

    print(answer)


async def main() -> None:
    kernel = build_kernel()

    print("Populating memory...")
    await populate_memory(kernel)
    print("Asking questions... (manually)")
    await search_memory_examples(kernel)
    print("Setting up a chat (with memory!)")
    chat_func, context = await setup_chat_with_memory(kernel)
    print("Begin chatting (type 'exit' to exit):")
    while True:
        await chat(kernel, chat_func, context)


if __name__ == "__main__":
    asyncio.run(main())
