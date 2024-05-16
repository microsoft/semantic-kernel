# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Callable, Coroutine

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.kernel_exceptions import OperationCancelledException
from semantic_kernel.filters.function.function_invocation_context import FunctionInvocationContext
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict

logger = logging.getLogger(__name__)


class ChatHistoryHooked(ChatHistory):
    async def function_filter(
        self,
        function_context: FunctionInvocationContext,
        next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
    ) -> None:
        if function_context.function.plugin_name != "chat":
            await next(function_context)
            return
        try:
            user_input = input("User:> ")
        except KeyboardInterrupt:
            raise OperationCancelledException("User stopped the operation")
        except EOFError:
            raise OperationCancelledException("User stopped the operation")
        if user_input == "exit":
            raise OperationCancelledException("User stopped the operation")
        self.add_user_message(user_input)

        await next(function_context)

        if function_context.result:
            logger.info(f'Usage: {function_context.result.metadata.get("usage")}')
            self.add_message(function_context.result.value[0])
            print(f"Mosscap:> {str(function_context.result)}")


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

    @kernel.filter("function_invocation")
    async def exception_catch_filter(context, next):
        try:
            await next(context)
        except Exception as e:
            logger.info(e)
            raise e

    kernel.add_filter("function_invocation", history)

    chatting = True
    while chatting:
        chatting = await kernel.invoke(
            function_name="chat",
            plugin_name="chat",
            chat_history=history,
        )


if __name__ == "__main__":
    asyncio.run(main())
