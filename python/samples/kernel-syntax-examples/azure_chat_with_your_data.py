# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import os
from pprint import pprint

from dotenv import load_dotenv

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = sk.Kernel()

data_source_config = sk_oai.AzureChatCompletionDataSourceConfig(
    endpoint=os.environ["AZURE_COGNITIVE_SEARCH_ENDPOINT"],
    key=os.environ["AZURE_COGNITIVE_SEARCH_KEY"],
    index_name=os.environ["AZURE_COGNITIVE_SEARCH_INDEX_NAME"],
)

kernel.add_chat_service(
    "chat-with-your-data",
    sk_oai.AzureChatCompletionWithData(
        **azure_openai_settings_from_dot_env_as_dict(include_api_version=False),
        data_source_configs=[data_source_config],
        api_version="2023-08-01-preview",  # This is the only supported API version
        logger=logging.getLogger("chat-with-your-data"),
    ),
)

prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
    max_tokens=2000, temperature=0.7, top_p=0.8
)

prompt_template = sk.ChatPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function(
    "ChatWithYourDataBot", "Chat", function_config
)


async def chat() -> bool:
    context_vars = sk.ContextVariables()

    try:
        user_input = input("User:> ")
        context_vars["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.run_async(chat_function, input_vars=context_vars)
    citations = answer.objects.get("tool", "{}")
    print(f"ChatWithYourDataBot:> {answer}")
    print("Tool message:>")
    pprint(json.loads(citations))
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
