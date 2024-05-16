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

logger = logging.getLogger(__name__)


async def input_output_filter(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
) -> None:
    if context.function.plugin_name != "chat":
        await next(context)
        return
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        raise OperationCancelledException("User stopped the operation")
    except EOFError:
        raise OperationCancelledException("User stopped the operation")
    if user_input == "exit":
        raise OperationCancelledException("User stopped the operation")
    context.arguments["chat_history"].add_user_message(user_input)

    await next(context)

    if context.result:
        logger.info(f'Usage: {context.result.metadata.get("usage")}')
        context.arguments["chat_history"].add_message(context.result.value[0])
        print(f"Mosscap:> {str(context.result)}")


async def main() -> None:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id="chat-gpt"))
    kernel.add_plugin(
        parent_directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), plugin_name="chat"
    )
    history = ChatHistory()

    kernel.add_filter("function_invocation", input_output_filter)

    @kernel.filter(filter_type="function_invocation")
    async def exception_catch_filter(
        context: FunctionInvocationContext, next: Coroutine[FunctionInvocationContext, Any, None]
    ):
        try:
            await next(context)
        except Exception as e:
            logger.info(e)
            raise e

    chatting = True
    while chatting:
        chatting = await kernel.invoke(
            function_name="chat",
            plugin_name="chat",
            chat_history=history,
        )


if __name__ == "__main__":
    asyncio.run(main())
