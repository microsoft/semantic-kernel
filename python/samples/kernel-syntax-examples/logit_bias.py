# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion
)
from semantic_kernel.connectors.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.open_ai as sk_oai


async def chat_request_example():
    # To use Logit Bias you will need to know the token ids of the words you want to use.
    # Getting the token ids using the GPT Tokenizer: https: // platform.openai.com/tokenizer
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_chat_service(
        "chat-gpt", sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )
    # The following text is the tokenized version of the book related tokens
    # novel literature reading author library story chapter paperback hardcover
    # ebook publishing fiction nonfiction manuscript textbook bestseller bookstore
    # reading list bookworm"
    keys = [
        3919, 626, 17201, 1300, 25782, 9800, 32016, 13571, 43582, 20189,
        1891, 10424, 9631, 16497, 12984, 20020, 24046, 13159, 805, 15817,
        5239, 2070, 13466, 32932, 8095, 1351, 25323
    ]
    # This will make the model try its best to avoid any of the above related words.
    settings = ChatRequestSettings()
    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for key in keys:
        # -100 to potentially ban all the tokens from the list.
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
    prompt_template.add_user_message("Hi, I'm looking some suggestions")
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
    answer = await kernel.run_async(chat_function, input_vars=None)
    print(f"Assistant:> {answer}")
    prompt_template.add_user_message(
        "I love history and philosophy, I'd like to learn something new about Greece, any suggestion?")
    answer = await kernel.run_async(chat_function, input_vars=None)
    print(f"Assistant:> {answer}")
    return


async def main() -> None:
    await chat_request_example()

if __name__ == "__main__":
    asyncio.run(main())
