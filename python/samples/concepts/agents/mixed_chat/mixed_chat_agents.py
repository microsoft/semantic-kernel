# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentSettings, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create a Azure AI Foundry Agent, 
a chat completion agent and have them participate in a group chat to work towards
the user's requirement.
"""


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


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


async def main():
    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 2. Create agents
        agent_writer = AzureAIAgent(
            client=client,
            definition=await client.agents.create_agent(
                model=AzureAIAgentSettings().model_deployment_name,
                name=COPYWRITER_NAME,
                instructions=COPYWRITER_INSTRUCTIONS,
            ),
        )
        agent_reviewer = ChatCompletionAgent(
            service=AzureChatCompletion(service_id="artdirector"),
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )

        # 3. Create the AgentGroupChat object and specify the list of agents along with the termination strategy
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        # 4. Provide the task an start running
        input = "a slogan for a new line of electric cars."
        await chat.add_chat_message(input)
        print(f"# {AuthorRole.USER}: '{input}'")
        async for content in chat.invoke():
            print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

        # 5. Done and remove the Auzre AI Foundry Agent.
        print(f"# IS COMPLETE: {chat.is_complete}")

        await client.agents.delete_agent(agent_writer.definition.id)


if __name__ == "__main__":
    asyncio.run(main())
