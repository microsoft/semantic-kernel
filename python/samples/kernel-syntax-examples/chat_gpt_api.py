# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose, unless asked a direct question, then you give a direct answer.
"""

kernel = sk.Kernel()

deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
api_version = "2023-07-01-preview"
chat_service = sk_oai.AzureChatCompletion(
    deployment_name,
    endpoint,
    api_key,
    api_version=api_version,
)
kernel.add_chat_service(
    "chat-gpt",
    chat_service,
)

prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
    max_tokens=2000, temperature=0.7, top_p=0.8
)

prompt_template = sk.ChatPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)

prompt_template.add_system_message(system_message)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message(
    "I am Mosscap, a chat bot. I'm trying to figure out what people need."
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)


async def chat(stream: bool = False) -> bool:
    context_vars = sk.ContextVariables()

    try:
        user_input = input("User:> ")
        context_vars["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False, None
    except EOFError:
        print("\n\nExiting chat...")
        return False, None

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False, None
    if user_input == "switch":
        return True, not stream

    if stream:
        print("Mosscap:> ", end="")
        async for answer in kernel.run_stream_async(
            chat_function, input_vars=context_vars
        ):
            if answer.content:
                print(answer.content, end="")
        print()
    else:
        answer = await kernel.run_async(chat_function, input_vars=context_vars)
        print(f"Mosscap:> {answer}")
    return True, None


async def main() -> None:
    chatting = True
    stream = True
    while chatting:
        chatting, stream_update = await chat(stream)
        if stream_update is not None:
            stream = stream_update
            print(f'Switch to {"streaming" if stream else "non-streaming"} mode')
            continue
        print(chat_service.usage)


if __name__ == "__main__":
    asyncio.run(main())
