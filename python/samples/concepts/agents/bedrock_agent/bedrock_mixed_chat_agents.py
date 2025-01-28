# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import dotenv

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

dotenv.load_dotenv()

# By default, this sample will create a new agent.
# If you want to use an existing agent, set this to False and fill in required parameters.
CREATE_NEW_AGENT = True

# If you want to enable streaming, set this to True.
# In order to perform streaming, you need to have the permission on action: bedrock:InvokeModelWithResponseStream
STREAMING = False

# Common parameters whether creating a new agent or using an existing agent
AGENT_ROLE_AMAZON_RESOURCE_NAME = os.getenv("AGENT_ROLE_AMAZON_RESOURCE_NAME")

# If creating a new agent, you need to specify the following:
# [Note] You may have to request access to the foundation model if you don't have it.
FOUNDATION_MODEL = os.getenv("FOUNDATION_MODEL")
INSTRUCTION = "You are a fridenly assistant. You help people find information."

# If using an existing agent, you need to specify the following:
AGENT_ID = ""


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
"""

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""


async def use_new_agent():
    """Create a new bedrock agent."""
    return await BedrockAgent.create_new_agent(
        agent_name=COPYWRITER_NAME,
        foundation_model=FOUNDATION_MODEL,
        role_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        instruction=COPYWRITER_INSTRUCTIONS,
    )


async def use_existing_agent():
    """Use an existing bedrock agent that has been created and prepared."""
    return await BedrockAgent.use_existing_agent(
        agent_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        agent_id=AGENT_ID,
        agent_name=COPYWRITER_NAME,
    )


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


def _create_kernel_with_chat_completion() -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion())
    return kernel


async def main():
    agent_reviewer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion(),
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    agent_writer = await use_new_agent() if CREATE_NEW_AGENT else await use_existing_agent()

    chat = AgentGroupChat(
        agents=[agent_writer, agent_reviewer],
        termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
    )

    input = "A slogan for a new line of electric cars."

    await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
    print(f"# {AuthorRole.USER}: '{input}'")

    if STREAMING:
        current_agent = "*"
        async for message_chunk in chat.invoke_stream():
            if current_agent != message_chunk.name:
                current_agent = message_chunk.name or "*"
                print(f"\n# {message_chunk.role} - {current_agent}: ", end="")
            print(message_chunk.content, end="")
    else:
        async for message in chat.invoke():
            print(f"# {message.role} - {message.name or '*'}: '{message.content}'")

    print(f"# IS COMPLETE: {chat.is_complete}")


if __name__ == "__main__":
    asyncio.run(main())
