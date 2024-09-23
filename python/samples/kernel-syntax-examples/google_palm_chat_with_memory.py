# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Tuple

import semantic_kernel as sk
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.prompt_template.input_variable import InputVariable

kernel = sk.Kernel()
apikey = sk.google_palm_settings_from_dot_env()
palm_text_embed = sk_gp.GooglePalmTextEmbedding("models/embedding-gecko-001", apikey)
kernel.add_service(palm_text_embed)
chat_service_id = "models/chat-bison-001"
palm_chat_completion = sk_gp.GooglePalmChatCompletion(chat_service_id, apikey)
kernel.add_service(palm_chat_completion)
kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=palm_text_embed)
kernel.import_plugin(sk.core_plugins.TextMemoryPlugin(), "TextMemoryPlugin")


async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the semantic memory
    await kernel.memory.save_information("aboutMe", id="info1", text="My name is Andrea")
    await kernel.memory.save_information("aboutMe", id="info2", text="I currently work as a tour guide")
    await kernel.memory.save_information("aboutMe", id="info3", text="My favorite hobby is hiking")
    await kernel.memory.save_information("aboutMe", id="info4", text="I visitied Iceland last year.")
    await kernel.memory.save_information("aboutMe", id="info5", text="My family is from New York")


async def search_memory_examples(kernel: sk.Kernel) -> None:
    questions = [
        "what's my name",
        "what is my favorite hobby?",
        "where's my family from?",
        "where did I travel last year?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await kernel.memory.search("aboutMe", question)
        print(f"Answer: {result}\n")


async def setup_chat_with_memory(
    kernel: sk.Kernel,
) -> Tuple[sk.KernelFunction, sk.KernelArguments]:
    """
    When using Google PaLM to chat with memories, a chat prompt template is
    essential; otherwise, the kernel will send text prompts to the Google PaLM
    chat service. Unfortunately, when a text prompt includes memory, chat
    history, and the user's current message, PaLM often struggles to comprehend
    the user's message. To address this issue, the prompt containing memory is
    incorporated into the chat prompt template as a system message.
    Note that this is only an issue for the chat service; the text service
    does not require a chat prompt template.
    """
    prompt = """
    ChatBot can have a conversation with you about any topic.
    It can give explicit instructions or say 'I don't know' if
    it does not have an answer.

    Information about me, from previous conversations:
    - {{$fact1}} {{recall $fact1}}
    - {{$fact2}} {{recall $fact2}}
    - {{$fact3}} {{recall $fact3}}
    - {{$fact4}} {{recall $fact4}}
    - {{$fact5}} {{recall $fact5}}

    """.strip()

    req_settings = kernel.get_service(chat_service_id).get_prompt_execution_settings_class()(service_id=chat_service_id)
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


async def chat(kernel: sk.Kernel, chat_func: sk.KernelFunction, arguments: sk.KernelArguments) -> bool:
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

    arguments["user_input"] = user_input
    answer = await kernel.invoke(chat_func, arguments)
    arguments["chat_history"].add_user_message(user_input)
    arguments["chat_history"].add_assistant_message(str(answer))

    print(f"ChatBot:> {answer}")
    return True


async def main() -> None:
    await populate_memory(kernel)
    await search_memory_examples(kernel)
    chat_func, arguments = await setup_chat_with_memory(kernel)
    print("Begin chatting (type 'exit' to exit):\n")
    chatting = True
    while chatting:
        chatting = await chat(kernel, chat_func, arguments)


if __name__ == "__main__":
    asyncio.run(main())
