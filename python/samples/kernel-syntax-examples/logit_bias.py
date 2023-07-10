# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.connectors.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.open_ai as sk_oai
import os


async def chat_request_example():
    # To use Logit Bias you will need to know the token ids of the words you want to use.
    # Getting the token ids using the GPT Tokenizer: https://platform.openai.com/tokenizer
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    openai_chat_completion = sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    kernel.add_chat_service("ChatBot", openai_chat_completion)

    # Spaces and capitalization affect the token ids.
    # The following is the token ids of basketball related words.
    keys = [2032, 680, 9612, 26675, 3438, 42483, 21265, 6057, 11230, 1404, 2484, 12494, 35, 822, 11108]
    banned_words = ["swish", 'screen', 'score', 'dominant', 'basketball', 'game', 'GOAT', 'Shooting', 'Dribbling']
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

    prompt_template.add_system_message("You are a basketball expert")
    user_mssg = "I love the LA Lakers, I'd like to learn something new about LeBron James, any suggestion?"
    prompt_template.add_user_message(user_mssg)
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
    answer = await kernel.run_async(chat_function, input_vars=None)
    context_vars["chat_history"] = f"User:> {user_mssg}\nChatBot:> {answer}\n"
    context_vars["chat_bot_ans"] = str(answer)
    return context_vars, banned_words


async def main() -> None:
    chat, banned_words = await chat_request_example()
    print("Chat completion example:")
    print("------------------------")
    print(chat["chat_history"])
    passed = True
    print("------------------------")
    chat_bot_ans_words = chat["chat_bot_ans"].split()
    for word in banned_words:
        if word in chat_bot_ans_words:
            print(f"The banned word \"{word}\" was found in the answer")
            passed = False
    if passed == True:
        print("None of the banned words were found in the answer")

    print("\n", "Text completion example:")
    print("------------------------")
    answer, user_mssg, banned_words = await text_complete_request_example()
    print("User:> " + user_mssg)
    print("ChatBot:> ", answer + "\n")
    passed = True
    for word in banned_words:
        if word in chat_bot_ans_words:
            print(f"The banned word \"{word}\" was found in the answer")
            passed = False
    if passed == True:
        print("None of the banned words were found in the answer")
    return


async def text_complete_request_example():
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()
    openai_text_completion = sk_oai.OpenAITextCompletion("text-davinci-002", api_key, org_id)
    kernel.add_text_completion_service("dv", openai_text_completion)

    # Spaces and capitalization affect the token ids.
    # The following is the token ids of pie related words.
    keys = [18040, 17180, 16108, 4196, 79, 931, 5116, 30089, 36724, 47, 931, 5116,
            431, 5171, 613, 5171, 350, 721, 272, 47, 721, 272]
    banned_words = ["apple", " apple", "Apple", " Apple", "pumpkin", " pumpkin",
                    " Pumpkin", "pecan", " pecan", " Pecan", "Pecan"]

    # This will make the model try its best to avoid any of the above related words.
    settings = CompleteRequestSettings()

    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for key in keys:
        # -100 to potentially ban all the tokens from the list.
        settings.token_selection_biases[key] = -100

    user_mssg = "The best pie flavor to have in autumn is"
    answer = await openai_text_completion.complete_async(user_mssg, settings)
    return answer, user_mssg, banned_words

if __name__ == "__main__":
    asyncio.run(main())
