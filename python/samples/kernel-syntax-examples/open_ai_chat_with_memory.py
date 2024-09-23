# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Tuple

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAITextEmbedding,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import KernelFunction
from semantic_kernel.prompt_template.input_variable import InputVariable

kernel = sk.Kernel()

api_key, org_id = sk.openai_settings_from_dot_env()
oai_text_embedding = OpenAITextEmbedding(
    service_id="oai_text_embed", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
)
service_id = "oai_chat"
oai_chat_service = OpenAIChatCompletion(
    service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id
)
kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=oai_text_embedding)
kernel.add_service(oai_chat_service)
kernel.add_service(oai_text_embedding)

kernel.import_plugin(sk.core_plugins.TextMemoryPlugin(), "text_memory")


async def populate_memory(kernel: sk.Kernel) -> None:
    await kernel.memory.save_information(collection="aboutMe", id="info1", text="My name is Andrea")
    await kernel.memory.save_information(collection="aboutMe", id="info2", text="I currently work as a tour guide")
    await kernel.memory.save_information(
        collection="aboutMe", id="info3", text="I've been living in Seattle since 2005"
    )
    await kernel.memory.save_information(
        collection="aboutMe",
        id="info4",
        text="I visited France and Italy five times since 2015",
    )
    await kernel.memory.save_information(collection="aboutMe", id="info5", text="My family is from New York")


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


async def setup_chat_with_memory(
    kernel: sk.Kernel,
) -> Tuple[KernelFunction, sk.KernelArguments]:
    prompt = """
        ChatBot can have a conversation with you about any topic.
        It can give explicit instructions or say 'I don't know' if
        it does not have an answer.

        Information about me, from previous conversations:
        {{$fact1}} {{recall $fact1}}
        {{$fact2}} {{recall $fact2}}
        {{$fact3}} {{recall $fact3}}
        {{$fact4}} {{recall $fact4}}
        {{$fact5}} {{recall $fact5}}

        {{$user_input}}

        """.strip()
    req_settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
    req_settings.max_tokens = 2000
    req_settings.temperature = 0.7
    req_settings.top_p = 0.8

    prompt_template_config = sk.PromptTemplateConfig(
        template="{{$user_input}}",
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(name="user_input", description="The user input", is_required=True),
            InputVariable(name="chat_history", description="The history of the conversation", is_required=True),
        ],
        execution_settings=req_settings,
    )

    chat_func = kernel.create_function_from_prompt(
        plugin_name="chat_memory", function_name="ChatWithMemory", prompt_template_config=prompt_template_config
    )

    chat_history = ChatHistory()
    chat_history.add_system_message(prompt)

    arguments = sk.KernelArguments(
        fact1="what is my name?",
        fact2="what is my favorite hobby?",
        fact3="where's my family from?",
        fact4="where did I travel last year?",
        fact5="what do I do for work?",
        collection="aboutMe",
        relevance=0.6,
        chat_history=chat_history,
    )

    return chat_func, arguments


async def chat(kernel: sk.Kernel, chat_func: KernelFunction, arguments: sk.KernelArguments) -> bool:
    try:
        user_input = input("User:> ")
        print(f"User:> {user_input}")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    arguments["user_input"] = user_input
    answer = await kernel.invoke(chat_func, arguments)
    arguments["chat_history"].add_user_message(user_input)
    arguments["chat_history"].add_system_message(str(answer))

    print(f"ChatBot:> {answer}")
    return True


async def main():
    print("Populating memory...")
    await populate_memory(kernel)

    print("Asking questions... (manually)")
    await search_memory_examples(kernel)

    print("Setting up a chat (with memory!)")
    chat_func, arguments = await setup_chat_with_memory(kernel)

    result = await chat(kernel=kernel, chat_func=chat_func, arguments=arguments)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
