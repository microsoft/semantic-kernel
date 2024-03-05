# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Any, Dict

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

"""
Logit bias enables prioritizing certain tokens within a given output.
To utilize the logit bias function, you will need to know the token ids of the words you are using.
See the GPT Tokenizer to obtain token ids: https://platform.openai.com/tokenizer
Read more about logit bias and how to configure output: https://help.openai.com/en/articles/5247780-using-logit-bias-to-define-token-probability
"""


def _config_ban_tokens(settings: PromptExecutionSettings, keys: Dict[Any, Any]):
    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for k in keys:
        # -100 to potentially ban all tokens in the list
        settings.logit_bias[k] = -100
    return settings


def _prepare_input_chat(chat: ChatHistory):
    return "".join([f"{msg.role}: {msg.content}\n" for msg in chat])


async def chat_request_example(kernel, api_key, org_id):
    service_id = "chat_service"
    openai_chat_completion = sk_oai.OpenAIChatCompletion(
        service_id=service_id, ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id
    )
    kernel.add_service(openai_chat_completion)

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
    settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
    settings = _config_ban_tokens(settings, keys)

    prompt_template_config = PromptTemplateConfig(
        template="{{$user_input}}",
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(
                name="user_input", description="The history of the conversation", is_required=True, default=""
            ),
        ],
        execution_settings=settings,
    )

    chat = ChatHistory()

    chat.add_user_message("Hi there, who are you?")
    chat.add_assistant_message("I am an AI assistant here to answer your questions.")

    chat_function = kernel.create_function_from_prompt(
        plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
    )

    chat.add_system_message("You are a basketball expert")
    chat.add_user_message("I love the LA Lakers, tell me an interesting fact about LeBron James.")

    answer = await kernel.invoke(chat_function, KernelArguments(user_input=_prepare_input_chat(chat)))
    chat.add_assistant_message(str(answer))

    chat.add_user_message("What are his best all-time stats?")
    answer = await kernel.invoke(chat_function, KernelArguments(user_input=_prepare_input_chat(chat)))
    chat.add_assistant_message(str(answer))

    print(chat)

    kernel.remove_all_services()

    return chat, banned_words


async def text_complete_request_example(kernel, api_key, org_id):
    service_id = "text_service"
    openai_text_completion = sk_oai.OpenAITextCompletion(
        service_id=service_id, ai_model_id="gpt-3.5-turbo-instruct", api_key=api_key, org_id=org_id
    )
    kernel.add_service(openai_text_completion)

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
    settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
    settings = _config_ban_tokens(settings, keys)

    prompt_template_config = PromptTemplateConfig(
        template="{{$user_input}}",
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(
                name="user_input", description="The history of the conversation", is_required=True, default=""
            ),
        ],
        execution_settings=settings,
    )

    chat = ChatHistory()

    chat.add_user_message("The best pie flavor to have in autumn is")

    text_function = kernel.create_function_from_prompt(
        plugin_name="TextBot", function_name="TextCompletion", prompt_template_config=prompt_template_config
    )

    answer = await kernel.invoke(text_function, KernelArguments(user_input=_prepare_input_chat(chat)))
    chat.add_assistant_message(str(answer))

    print(chat)

    kernel.remove_all_services()

    return chat, banned_words


def _check_banned_words(banned_list, actual_list) -> bool:
    passed = True
    for word in banned_list:
        if word in actual_list:
            print(f'The banned word "{word}" was found in the answer')
            passed = False
    return passed


def _format_output(chat, banned_words) -> None:
    print("--- Checking for banned words ---")
    chat_bot_ans_words = [word for msg in chat.messages if msg.role == "assistant" for word in msg.content.split()]
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
