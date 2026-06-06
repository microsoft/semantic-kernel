# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin

"""
This sample demonstrates how to create a Semantic Kernel agent with access
to the TWZRD Agent Intel MCP server (https://intel.twzrd.xyz) for trust scoring
and x402 payment verification of AI agents on Solana.

TWZRD Agent Intel is a zero-install remote MCP server that provides:
- score_agent(wallet): Returns trust score (0-100) and reputation data
- resolve_agent(wallet): Agent identity resolution
- preflight_check(wallet): Pre-transaction safety check
- verify_trust_receipt(receipt): Verify x402 payment receipts

MCP config: {"mcpServers": {"twzrd-agent-intel": {"url": "https://intel.twzrd.xyz/mcp"}}}

Required environment variables:
- OPENAI_API_KEY
- OPENAI_CHAT_MODEL_ID (e.g. gpt-4o-mini)
"""

# Example agent wallets to check
USER_INPUTS = [
    "What is the trust score for Solana wallet D1QkbFJKiPsymJ65RKHhF6DFB8sPMfpBaFBzuHKfJGWi?",
    "Run a preflight check on wallet 4Nd1mFxXgSU4LJSS2aWUKf6vXhiGaWMPBJXQWgpjvPdT before proceeding.",
]


async def main():
    # 1. Create TWZRD Agent Intel MCP plugin (no API key needed — free tier)
    async with MCPStreamableHttpPlugin(
        name="TwzrdAgentIntel",
        description="Trust scoring and x402 payment verification for AI agents on Solana",
        url="https://intel.twzrd.xyz/mcp",
    ) as twzrd_plugin:
        # 2. Create the agent with TWZRD tools available
        agent = ChatCompletionAgent(
            service=OpenAIChatCompletion(),
            name="TrustVerificationAgent",
            instructions=(
                "You are a trust verification agent. "
                "Use the TWZRD Agent Intel tools to score agent wallets, run preflight checks, "
                "and verify x402 payment receipts. "
                "A trust score >= 70 is high trust, 40-70 is medium, < 40 is low. "
                "Always recommend caution for wallets with low trust scores."
            ),
            plugins=[twzrd_plugin],
        )

        for user_input in USER_INPUTS:
            thread: ChatHistoryAgentThread | None = None

            print(f"# User: {user_input}")
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response}\n")
            thread = response.thread

            await thread.delete() if thread else None


"""
Sample output:

# User: What is the trust score for Solana wallet D1QkbFJKiPsymJ65RKHhF6DFB8sPMfpBaFBzuHKfJGWi?
# TrustVerificationAgent: I checked the TWZRD Agent Intel trust score for wallet
  D1QkbFJKiPsymJ65RKHhF6DFB8sPMfpBaFBzuHKfJGWi.
  Trust Score: 82/100 — High Trust
  This agent has a strong track record of successful x402 transactions and consistent activity.
  It is generally safe to interact with this agent.

# User: Run a preflight check on wallet 4Nd1mFxXgSU4LJSS2aWUKf6vXhiGaWMPBJXQWgpjvPdT ...
# TrustVerificationAgent: Preflight check complete for 4Nd1mFxXgSU4LJSS2aWUKf6vXhiGaWMPBJXQWgpjvPdT.
  Result: safe_to_transact = false
  Reason: Wallet has insufficient transaction history for reliable trust scoring.
  Recommendation: Proceed with caution or request additional identity verification.
"""

if __name__ == "__main__":
    asyncio.run(main())
