# noqa: CPY001
# /// script
# dependencies = [
#   "semantic-kernel[mcp]",
# ]
# ///
# Copyright (c) Microsoft. All rights reserved.
import argparse
from typing import Literal

import anyio

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.mcp import MCPPluginBase, MCPSsePlugin, MCPStdioPlugin
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel import Kernel


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Semantic Kernel as MCP host.")

    parser.add_argument(
        "--transport",
        type=str,
        choices=["sse", "stdio"],
        default="stdio",
        help="Transport method to use (default: stdio).",
    )

    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="MCP Server URL for non-stdio transports",
    )

    return parser.parse_args()


async def main(transport: Literal["sse", "stdio"] = "stdio", url: str | None = None):
    chat_completion_service = OpenAIChatCompletion(
        service_id="default",
    )

    kernel = Kernel()
    kernel.add_service(chat_completion_service)

    mcp_client_plugin: MCPPluginBase | None = None

    if transport == "stdio":
        mcp_client_plugin = MCPStdioPlugin(
            name="Echo",
            description="SK Echo Plugin",
            command="uv",
            args=[
                "run",
                "sk_mcp_server.py",
            ],
        )
    elif transport == "sse":
        mcp_client_plugin = MCPSsePlugin(
            name="Echo",
            url=url,
            description="SK Echo plugin",
        )

    async with mcp_client_plugin as plugin:
        _ = kernel.add_plugin(plugin)

        chat_history = ChatHistory()
        chat_history.add_developer_message("You're a helpful assistant that echos user prompts.")
        chat_history.add_user_message("repeat hello world")

        response: ChatMessageContent | None = await chat_completion_service.get_chat_message_content(
            chat_history=chat_history,
            settings=OpenAIChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
            ),
            kernel=kernel,
        )

        if response is None:
            raise ValueError("No response returned from chat completion service")

        print(f"Assistant > {response.content}")


if __name__ == "__main__":
    args = parse_arguments()
    anyio.run(main, args.transport, args.url)
