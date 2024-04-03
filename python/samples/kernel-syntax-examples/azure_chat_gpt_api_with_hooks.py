# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import asyncio
import os

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.hooks import PostFunctionInvokeContext, PreFunctionInvokeContext, kernel_hook_filter
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict


class ChatHistoryHooked(ChatHistory):
    @kernel_hook_filter(include_functions=["chat"])
    async def pre_function_invoke(self, context: PreFunctionInvokeContext) -> None:
        try:
            user_input = input("User:> ")
        except KeyboardInterrupt:
            context.cancel()
            return
        except EOFError:
            context.cancel()
            return
        if user_input == "exit":
            context.cancel()
            return
        self.add_user_message(user_input)

    @kernel_hook_filter(include_functions=["chat"])
    async def post_function_invoke(self, context: PostFunctionInvokeContext) -> None:
        self.add_message(context.function_result.value[0])
        print(f"Mosscap:> {context.function_result}")

    def pre_prompt_render(self, context):
        print(f"{context.arguments=}")

    def post_prompt_render(self, context):
        print(f"{context.rendered_prompt=}")


@kernel_hook_filter(include_functions=["chat"])
def post_function_invoke(context: PostFunctionInvokeContext) -> None:
    print(f"usage was: {context.function_result.get_inner_content(0).usage}")


async def main() -> None:
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            service_id="chat-gpt", **azure_openai_settings_from_dot_env_as_dict(include_api_version=True)
        )
    )
    kernel.import_plugin_from_prompt_directory(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), "chat"
    )
    history = ChatHistoryHooked()
    kernel.add_hook(hook=history)
    kernel.add_hook(hook=post_function_invoke)
    kernel.add_hook(lambda context: print("\nRun after func..."), "post_function_invoke")

    chatting = True
    while chatting:
        chatting = await kernel.invoke(
            function_name="chat",
            plugin_name="chat",
            chat_history=history,
        )


if __name__ == "__main__":
    asyncio.run(main())
