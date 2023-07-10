# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.connectors.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.open_ai as sk_oai
import os


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
    context_vars = sk.ContextVariables()
    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for key in keys:
        # -100 to potentially ban all the tokens from the list.
        settings.token_selection_biases[key] = -100

    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
    )

    prompt_template = sk.ChatPromptTemplate(
        "{{$user_input}}", kernel.prompt_template_engine, prompt_config
    )

    prompt_template.add_system_message("You are a librarian expert")
    user_mssg = "Hi, I'm looking some suggestions"
    prompt_template.add_user_message(user_mssg)
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
    answer = await kernel.run_async(chat_function, input_vars=None)
    context_vars["chat_history"] = f"User:> {user_mssg}\nChatBot:> {answer}\n"
    context_vars["chat_bot_ans"] = str(answer)
    user_mssg = "I love history and philosophy, I'd like to learn something new about Greece, any suggestion?"
    prompt_template.add_user_message(user_mssg)
    answer = await kernel.run_async(chat_function, input_vars=None)
    context_vars["chat_history"] += f"\nUser:> {user_mssg}\nChatBot:> {answer}\n"
    context_vars["chat_bot_ans"] += '\n' + str(answer)

    return context_vars


async def main() -> None:
    chat = await chat_request_example()
    print("Chat content:")
    print("------------------------")
    print(chat["chat_history"])
    banned_words = ["novel", "literature", "reading", "author", "library",
                    "story", "chapter", "paperback", "hardcover", "ebook",
                    "publishing", "fiction", "nonfiction", "manuscript",
                    "textbook", "bestseller", "bookstore", "reading list",
                    "bookworm"]
    passed = True
    for word in banned_words:
        if word in chat["chat_bot_ans"]:
            print("The banned word " + word + " was found in the answer")
            passed = False
    if passed == True:
        print("None of the banned words were not found in the answer")

    await text_complete_request_example()
    return


async def text_complete_request_example():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        "dv", sk_oai.OpenAITextCompletion("text-davinci-002", api_key, org_id)
    )
    kernel.add_text_embedding_generation_service(
        "ada", sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id)
    )
    # "apple banana blueberry cherry chocolate coconut key lime lemon meringue pecan pumpkin raspberry strawberry vanilla"
    keys = [18040, 25996, 4171, 8396, 23612, 11311, 20132, 1994, 28738,
            18873, 285, 1586, 518, 613, 5171, 30089, 38973, 41236, 16858]

    # This will make the model try its best to avoid any of the above related words.
    settings = CompleteRequestSettings()

    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for key in keys:
        # -100 to potentially ban all the tokens from the list.
        settings.token_selection_biases[key] = -100

    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
    )
    prompt_template = sk.PromptTemplate(
        "The best pie flavor to have in autumn is", kernel.prompt_template_engine,
        prompt_config
    )
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("TextComplete", "Text", function_config)

    answer = await kernel.run_async(chat_function, input_vars=None)
    print(answer)
    return


if __name__ == "__main__":
    asyncio.run(main())
