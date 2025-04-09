# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys

from agents.auditor_agent import BrandAuditor
from agents.tagline_agent import TaglineGenerator
from dotenv import load_dotenv

from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create a group chat with Copilot Studio agents
to generate and evaluate taglines according to brand guidelines.
"""

# Load environment variables from .env file
load_dotenv()

# Configure the root logger to capture logs from all modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,  # Explicitly set output to stdout
    force=True  # Force reconfiguration of the root logger
)

# Set log levels for specific libraries that might be too verbose
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate based on brand approval."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        # Terminate if the brand auditor approves the tagline
        content = history[-1].content.lower()
        return "approved" in content and "not approved" not in content and "rejected" not in content


USER_INPUT = "Suggest a thrilling tagline for our energy drink that helps users crush the day."


async def main():
    # 1. Create the tagline generator agent
    tagline_generator = TaglineGenerator()
    
    # 2. Create the brand auditor agent
    brand_auditor = BrandAuditor()
    
    # 3. Place the agents in a group chat with a custom termination strategy
    chat = AgentGroupChat(
        agents=[tagline_generator, brand_auditor],
        termination_strategy=ApprovalTerminationStrategy(
            agents=[brand_auditor],
            maximum_iterations=10,
        ),
    )

    try:
        # 4. Add the user input to the chat
        await chat.add_chat_message(USER_INPUT)
        print(f"# {AuthorRole.USER}: '{USER_INPUT}'")
        
        # 5. Invoke the chat and print responses
        async for content in chat.invoke():
            print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
    finally:
        # 6. Reset the chat (cleanup)
        await chat.reset()

    """
    Sample Output:
    # AuthorRole.USER: Suggest a thrilling tagline for our energy drink that helps users crush the day.
    # AuthorRole.ASSISTANT - tagline_generator: "Fuel Your Fire, Crush the Day!"
    # AuthorRole.ASSISTANT - brand_auditor: "The tagline does not align with the brand's calm, confident,
    #  and sincere voice..."
    # AuthorRole.ASSISTANT - tagline_generator: "Empower Your Day with Natural Energy."
    # AuthorRole.ASSISTANT - brand_auditor: "The tagline aligns well with the brand's calm, confident,
    # and sincere voice..."
    """


if __name__ == "__main__":
    asyncio.run(main())
