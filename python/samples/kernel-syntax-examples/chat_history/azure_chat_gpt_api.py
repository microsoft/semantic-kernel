# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Tuple

from dotenv import load_dotenv

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel import Kernel
from semantic_kernel.connectors.chat_history.file_chat_history import FileChatHistory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict

load_dotenv()

# Minimal Kernel setup with just the api for chat.
kernel = Kernel()
kernel.add_chat_service(
    "chat-gpt",
    sk_oai.AzureChatCompletion(
        **azure_openai_settings_from_dot_env_as_dict(include_api_version=True)
    ),
)


async def get_history_and_function(filename: str) -> Tuple[FileChatHistory, SKFunction]:
    """Get the chat history and function."""

    # load the history from the file, including the template and prompt config
    chat_history = await FileChatHistory.load_async_from_store(
        kernel,
        filename,
    )

    # register the chat function
    # done every time incase the prompt config has changed in the file
    chat_function = kernel.register_semantic_function(
        "ChatBot",
        "Chat",
        SemanticFunctionConfig(
            chat_history.prompt_config, chat_history.chat_prompt_template
        ),
    )
    return chat_history, chat_function


async def stateless_chat(filename: str) -> bool:
    """Fully stateless version of chat."""
    # load the history from the file, including the template and prompt config
    chat_history, chat_function = await get_history_and_function(filename)
    context_vars = ContextVariables()
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

    answer = await chat_function.invoke_async(variables=context_vars)
    print(f"Mosscap:> {answer}")

    # save the history to the file, including the template and prompt config
    await chat_history.save_async()
    return True


async def main() -> None:
    filename = "samples/kernel-syntax-examples/chat_history/chat_history.json"
    chatting = True
    while chatting:
        chatting = await stateless_chat(filename)


if __name__ == "__main__":
    asyncio.run(main())
