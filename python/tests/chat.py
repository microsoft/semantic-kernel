# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk

sk_prompt = """
ChatBot can have a conversation with you about any topic.
It can give explicit instructions or say 'I don't know'
when it doesn't know the answer.

{{$chat_history}}
User:> {{$user_input}}
ChatBot:>
"""

kernel = sk.create_kernel()

api_key, org_id = sk.openai_settings_from_dot_env()
kernel.config.add_openai_completion_backend(
    "davinci-003", "text-davinci-003", api_key, org_id
)

prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
    max_tokens=2000, temperature=0.7, top_p=0.4
)

prompt_template = sk.PromptTemplate(
    sk_prompt, kernel.prompt_template_engine, prompt_config
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)


async def chat() -> None:
    context = sk.ContextVariables()
    context["chat_history"] = ""

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

    answer = await kernel.run_on_vars_async(context, chat_function)
    context["chat_history"] += f"\nUser:> {user_input}\nChatBot:> {answer}\n"

    print(f"ChatBot:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
