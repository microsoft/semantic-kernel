# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings


# See Example49_LogitBias.cs for original example
async def chat_request_example():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_chat_service(
        "chat-gpt", sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )

    # Tokens corresponding to:
    # "novel literature reading author library story chapter paperback hardcover ebook publishing fiction nonfiction manuscript textbook bestseller bookstore reading list bookworm"
    keys = [
        3919, 626, 17201, 1300, 25782, 9800, 32016, 13571, 43582, 20189,
        1891, 10424, 9631, 16497, 12984, 20020, 24046, 13159, 805, 15817,
        5239, 2070, 13466, 32932, 8095, 1351, 25323
    ]

    settings = ChatRequestSettings()

    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for key in keys:
        # For this example, each key is mapped to a value of -100
        settings.token_selection_biases[key] = -100

    print("Chat content:")
    print("------------------------")

    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
    )

    prompt_template = sk.ChatPromptTemplate(
        "{{$user_input}}", kernel.prompt_template_engine, prompt_config
    )

    prompt_template.add_system_message("You are a librarian expert")
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)

    first_user_msg = "Hi, I'm looking some suggestions"
    print(f"User: {first_user_msg}")
    print("------------------------")
    prompt_template.add_user_message(first_user_msg)
    answer = await kernel.run_async(chat_function, input_vars=None)
    print(f"Bot: {answer}")
    print("------------------------")

    second_user_msg = "I love history and philosophy, I'd like to learn something new about Greece, any suggestion?"
    print(f"User: {second_user_msg}")
    print("------------------------")
    prompt_template.add_user_message(second_user_msg)
    answer = await kernel.run_async(chat_function, input_vars=None)
    print(f"Bot: {answer}")
    print("------------------------")

    return


async def main() -> None:
    await chat_request_example()

if __name__ == "__main__":
    asyncio.run(main())
