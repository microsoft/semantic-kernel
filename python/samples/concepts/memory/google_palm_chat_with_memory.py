# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel import Kernel
from semantic_kernel.core_plugins import TextMemoryPlugin
from semantic_kernel.functions import KernelFunction
from semantic_kernel.memory import SemanticTextMemory, VolatileMemoryStore
from semantic_kernel.prompt_template import PromptTemplateConfig

collection_id = "generic"


async def populate_memory(memory: SemanticTextMemory) -> None:
    # Add some documents to the semantic memory
    await memory.save_information(collection=collection_id, id="info1", text="Your budget for 2024 is $100,000")
    await memory.save_information(collection=collection_id, id="info2", text="Your savings from 2023 are $50,000")
    await memory.save_information(collection=collection_id, id="info3", text="Your investments are $80,000")


async def search_memory_examples(memory: SemanticTextMemory) -> None:
    questions = ["What is my budget for 2024?", "What are my savings from 2023?", "What are my investments?"]

    for question in questions:
        print(f"Question: {question}")
        result = await memory.search(collection_id, question)
        print(f"Answer: {result[0].text}\n")


async def setup_chat_with_memory(
    kernel: Kernel,
    service_id: str,
) -> KernelFunction:
    prompt = """
    ChatBot can have a conversation with you about any topic.
    It can give explicit instructions or say 'I don't know' if
    it does not have an answer.

    Information about me, from previous conversations:
    - {{recall 'budget by year'}} What is my budget for 2024?
    - {{recall 'savings from previous year'}} What are my savings from 2023?
    - {{recall 'investments'}} What are my investments?

    {{$request}}
    """.strip()

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        execution_settings={service_id: kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)},
    )

    return kernel.add_function(
        function_name="chat_with_memory",
        plugin_name="TextMemoryPlugin",
        prompt_template_config=prompt_template_config,
    )


async def chat(kernel: Kernel, chat_func: KernelFunction) -> bool:
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

    answer = await kernel.invoke(chat_func, request=user_input)

    print(f"ChatBot:> {answer}")
    return True


async def main() -> None:
    kernel = Kernel()
    model_id = "models/embedding-gecko-001"
    palm_text_embed = sk_gp.GooglePalmTextEmbedding(model_id)
    kernel.add_service(palm_text_embed)
    chat_service_id = "models/chat-bison-001"
    palm_chat_completion = sk_gp.GooglePalmChatCompletion(chat_service_id)
    kernel.add_service(palm_chat_completion)

    memory = SemanticTextMemory(storage=VolatileMemoryStore(), embeddings_generator=palm_text_embed)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    print("Populating memory...")
    await populate_memory(memory)

    print("Asking questions... (manually)")
    await search_memory_examples(memory)

    print("Setting up a chat (with memory!)")
    chat_func = await setup_chat_with_memory(kernel, chat_service_id)

    print("Begin chatting (type 'exit' to exit):\n")
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  Try asking a question about your finances (i.e. \"talk to me about my finances\")."
    )
    chatting = True
    while chatting:
        chatting = await chat(kernel, chat_func)


if __name__ == "__main__":
    asyncio.run(main())
