"""Semantic Kernel + emem MCP example — multi-step verification: locate, recall, verify.

Connects a Microsoft Semantic Kernel agent to the emem MCP server over
Streamable HTTP and runs a multi-step verification chain for South Mumbai:
resolve the place, recall elevation, then verify the receipt/fact CID.

Install:
    pip install semantic-kernel

Usage:
    export OPENAI_API_KEY="sk-..."
    python emem_mcp_geospatial_agent.py

The agent will resolve South Mumbai, recall its elevation, then verify
the receipt/fact CID, showing each step in the chain.
"""

import asyncio
import os

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin

EMEM_MCP_URL = os.getenv("EMEM_MCP_URL", "https://emem.dev/mcp")

USER_INPUTS = [
    (
        "Using emem, resolve South Mumbai, recall its elevation "
        "(copdem30m.elevation_mean), then verify the receipt/fact CID. "
        "Show each step: locate, recall, verify."
    ),
    "Is the air quality in Delhi safe for outdoor exercise right now? Give me a signed fact with a receipt I can cite.",
    "Has there been recent deforestation near the Amazon at -3.47° N, -62.22° W?",
]


async def main() -> None:
    async with MCPStreamableHttpPlugin(
        name="emem",
        description="Shared, verifiable Earth memory — signed facts for any place on Earth",
        url=EMEM_MCP_URL,
    ) as emem_plugin:
        agent = ChatCompletionAgent(
            service=OpenAIChatCompletion(ai_model_id="gpt-4o"),
            name="GeospatialAgent",
            instructions=(
                "You are a geospatial verification agent grounded in emem's signed Earth memory. "
                "For every place query: "
                "1. Call emem_locate to resolve the place to a canonical cell64 address. "
                "2. Call emem_recall to read signed facts (air quality, elevation, flood extent, etc.). "
                "3. Report the emem:fact: receipt so the user can verify it offline. "
                "Always cite the fact_cid from the receipt."
            ),
            plugins=[emem_plugin],
        )

        thread: ChatHistoryAgentThread | None = None

        for user_input in USER_INPUTS:
            print(f"\n# User: {user_input}")
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response}")
            thread = response.thread

        await thread.delete() if thread else None


if __name__ == "__main__":
    asyncio.run(main())
