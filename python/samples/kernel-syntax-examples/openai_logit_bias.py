# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Any, Dict

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

"""
Logit bias enables prioritizing certain tokens within a given output.
To utilize the logit bias function, you will need to know the token ids of the words you are using.
See the GPT Tokenizer to obtain token ids: https://platform.openai.com/tokenizer
Read more about logit bias and how to configure output: https://help.openai.com/en/articles/5247780-using-logit-bias-to-define-token-probability
"""


def _config_ban_tokens(settings: AIRequestSettings, keys: Dict[Any, Any]):
    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for k in keys:
        # -100 to potentially ban all tokens in the list
        settings.logit_bias[k] = -100
    return settings


async def chat_request_example(kernel, api_key, org_id):
    openai_chat_completion = sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    kernel.add_chat_service("chat_service", openai_chat_completion)

    # Spaces and capitalization affect the token ids.
    # The following is the token ids of basketball related words.
    keys = [
        2032,
        680,
        9612,
        26675,
        3438,
        42483,
        21265,
        6057,
        11230,
        1404,
        2484,
        12494,
        35,
        822,
        11108,
    ]
    banned_words = [
        "swish",
        "screen",
        "score",
        "dominant",
        "basketball",
        "game",
        "GOAT",
        "Shooting",
        "Dribbling",
    ]

    # Model will try its best to avoid using any of the above words
    settings = kernel.get_request_settings_from_service(ChatCompletionClientBase, "chat_service")
    settings = _config_ban_tokens(settings, keys)

    prompt_config = sk.PromptTemplateConfig.from_execution_settings(max_tokens=2000, temperature=0.7, top_p=0.8)
    prompt_template = sk.ChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)

    # Setup chat with prompt
    prompt_template.add_system_message("You are a basketball expert")
    user_mssg = "I love the LA Lakers, tell me an interesting fact about LeBron James."
    prompt_template.add_user_message(user_mssg)
    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    kernel.register_semantic_function("ChatBot", "Chat", function_config)

    chat_messages = []
    messages = [{"role": "user", "content": user_mssg}]

    chat_messages.append(("user", user_mssg))
    answer = await openai_chat_completion.complete_chat_async(messages=messages, settings=settings)
    chat_messages.append(("assistant", str(answer[0])))

    user_mssg = "What are his best all-time stats?"
    messages = [{"role": "user", "content": user_mssg}]
    chat_messages.append(("user", user_mssg))
    answer = await openai_chat_completion.complete_chat_async(messages=messages, settings=settings)
    chat_messages.append(("assistant", str(answer[0])))

    context_vars = sk.ContextVariables()
    context_vars["chat_history"] = ""
    context_vars["chat_bot_ans"] = ""
    for role, mssg in chat_messages:
        if role == "user":
            context_vars["chat_history"] += f"User:> {mssg}\n"
        elif role == "assistant":
            context_vars["chat_history"] += f"ChatBot:> {mssg}\n"
            context_vars["chat_bot_ans"] += f"{mssg}\n"

    kernel.remove_chat_service("chat_service")
    return context_vars, banned_words


async def text_complete_request_example(kernel, api_key, org_id):
    openai_text_completion = sk_oai.OpenAITextCompletion("gpt-3.5-turbo-instruct", api_key, org_id)
    kernel.add_text_completion_service("text_service", openai_text_completion)

    # Spaces and capitalization affect the token ids.
    # The following is the token ids of pie related words.
    keys = [
        18040,
        17180,
        16108,
        4196,
        79,
        931,
        5116,
        30089,
        36724,
        47,
        931,
        5116,
        431,
        5171,
        613,
        5171,
        350,
        721,
        272,
        47,
        721,
        272,
    ]
    banned_words = [
        "apple",
        " apple",
        "Apple",
        " Apple",
        "pumpkin",
        " pumpkin",
        " Pumpkin",
        "pecan",
        " pecan",
        " Pecan",
        "Pecan",
    ]

    # Model will try its best to avoid using any of the above words
    settings = kernel.get_request_settings_from_service(TextCompletionClientBase, "text_service")
    settings = _config_ban_tokens(settings, keys)

    user_mssg = "The best pie flavor to have in autumn is"
    answer = await openai_text_completion.complete_async(user_mssg, settings)

    context_vars = sk.ContextVariables()
    context_vars["chat_history"] = f"User:> {user_mssg}\nChatBot:> {answer}\n"
    context_vars["chat_bot_ans"] = str(answer)

    kernel.remove_text_completion_service("text_service")
    return context_vars, banned_words


def _check_banned_words(banned_list, actual_list) -> bool:
    passed = True
    for word in banned_list:
        if word in actual_list:
            print(f'The banned word "{word}" was found in the answer')
            passed = False
    return passed


def _format_output(context, banned_words) -> None:
    print(context["chat_history"])
    chat_bot_ans_words = context["chat_bot_ans"].split()
    if _check_banned_words(banned_words, chat_bot_ans_words):
        print("None of the banned words were found in the answer")


async def main() -> None:
    kernel = sk.Kernel()
    api_key, org_id = sk.openai_settings_from_dot_env()

    print("Chat completion example:")
    print("------------------------")
    chat, banned_words = await chat_request_example(kernel, api_key, org_id)
    _format_output(chat, banned_words)

    print("------------------------")

    print("\nText completion example:")
    print("------------------------")
    chat, banned_words = await text_complete_request_example(kernel, api_key, org_id)
    _format_output(chat, banned_words)

    return


if __name__ == "__main__":
    asyncio.run(main())
