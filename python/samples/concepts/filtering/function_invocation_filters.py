# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from collections.abc import Callable, Coroutine
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.exceptions import OperationCancelledException
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext

logger = logging.getLogger(__name__)


# A filter is a piece of custom code that runs at certain points in the process
# this sample has a filter that is called during Function Invocation for non-streaming function.
# You can name the function itself with arbitrary names, but the signature needs to be:
# `context, next`
# You are then free to run code before the call to the next filter or the function itself.
# and code afterwards.
async def input_output_filter(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
) -> None:
    if context.function.plugin_name != "chat":
        await next(context)
        return
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError) as exc:
        raise OperationCancelledException("User stopped the operation") from exc
    if user_input == "exit":
        raise OperationCancelledException("User stopped the operation")
    context.arguments["chat_history"].add_user_message(user_input)

    await next(context)

    if context.result:
        logger.info(f"Usage: {context.result.metadata.get('usage')}")
        context.arguments["chat_history"].add_message(context.result.value[0])
        print(f"Mosscap:> {context.result!s}")


async def main() -> None:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id="chat-gpt"))
    kernel.add_plugin(
        parent_directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), plugin_name="chat"
    )
    history = ChatHistory()

    # here we are adding two filters, one that was created earlier, and can be reused and added to other kernels
    # and one created and added in one go through the decorator
    kernel.add_filter("function_invocation", input_output_filter)

    # you can use both the literal term and the FilterTypes enum
    @kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
    async def exception_catch_filter(
        context: FunctionInvocationContext, next: Coroutine[FunctionInvocationContext, Any, None]
    ):
        try:
            await next(context)
        except Exception as e:
            logger.info(e)

    chatting = True
    while chatting:
        chatting = await kernel.invoke(
            function_name="chat",
            plugin_name="chat",
            chat_history=history,
        )


if __name__ == "__main__":
    asyncio.run(main())
