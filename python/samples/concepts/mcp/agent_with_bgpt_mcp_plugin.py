# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity import AzureCliCredential

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin

"""
This sample demonstrates how to connect a ChatCompletionAgent
to the BGPT MCP Server using the MCPStreamableHttpPlugin.

BGPT provides evidence-based retrieval over scientific literature
through a remote MCP server.

It uses the Azure OpenAI service to create an agent. Make sure the
following environment variables are configured:

- AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
- Optionally: AZURE_OPENAI_API_KEY

If no API key is configured, AzureCliCredential can also be used.
"""


# Example biomedical question
USER_INPUTS = [
    "Find recent papers about CRISPR gene editing in wheat.",
]


async def main() -> None:
    # Create the BGPT MCP plugin
    async with MCPStreamableHttpPlugin(
        name="BGPT",
        description="BGPT Scientific Literature Search",
        url="https://bgpt.pro/mcp/stream",
    ) as bgpt_plugin:

        # Create the agent
        agent = ChatCompletionAgent(
            service=AzureChatCompletion(
                credential=AzureCliCredential(),
            ),
            name="BGPTAgent",
            instructions=(
                "You are a biomedical research assistant. "
                "Use the BGPT MCP server to retrieve and summarize "
                "scientific evidence."
            ),
            plugins=[bgpt_plugin],
        )

        for user_input in USER_INPUTS:
            thread: ChatHistoryAgentThread | None = None

            print(f"# User: {user_input}")

            response = await agent.get_response(
                messages=user_input,
                thread=thread,
            )

            print(f"# {response.name}: {response}")

            thread = response.thread

            if thread:
                await thread.delete()


if __name__ == "__main__":
    asyncio.run(main())