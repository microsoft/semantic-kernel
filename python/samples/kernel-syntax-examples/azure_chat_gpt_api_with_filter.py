# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import asyncio
import os
from typing import Any, Callable, Coroutine

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.kernel_exceptions import OperationCancelledException
from semantic_kernel.hooks.function.function_hook_context_base import FunctionContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict


class ChatHistoryHooked(ChatHistory):
    async def function_filter(
        self,
        function_context: FunctionContext,
        next: Callable[[FunctionContext], Coroutine[Any, Any, FunctionContext]],
    ) -> FunctionContext:
        if function_context.function.plugin_name != "chat":
            return await next(function_context)
        try:
            user_input = input("User:> ")
        except KeyboardInterrupt:
            raise OperationCancelledException("User stopped the operation")
        except EOFError:
            raise OperationCancelledException("User stopped the operation")
        if user_input == "exit":
            raise OperationCancelledException("User stopped the operation")
        self.add_user_message(user_input)

        function_context = await next(function_context)

        if function_context.result:
            self.add_message(function_context.result.value[0])
            print(f"Mosscap:> {str(function_context.result)}")
        return function_context


async def main() -> None:
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            service_id="chat-gpt", **azure_openai_settings_from_dot_env_as_dict(include_api_version=True)
        )
    )
    kernel.add_plugin(
        parent_directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), plugin_name="chat"
    )
    history = ChatHistoryHooked()
    kernel.add_filter(history)

    chatting = True
    while chatting:
        chatting = await kernel.invoke(
            function_name="chat",
            plugin_name="chat",
            chat_history=history,
        )


if __name__ == "__main__":
    asyncio.run(main())
