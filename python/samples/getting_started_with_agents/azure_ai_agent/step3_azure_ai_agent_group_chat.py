# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create an OpenAI assistant using either
Azure OpenAI or OpenAI, a chat completion agent and have them participate in a
group chat to work towards the user's requirement.
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
If so, state that it is approved.  Do not use the word "approve" unless you are giving approval.
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

TASK = "a slogan for a new line of electric cars."


async def main():
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create the reviewer agent on the Azure AI agent service
        reviewer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )

        # 2. Create a Semantic Kernel agent for the reviewer Azure AI agent
        agent_reviewer = AzureAIAgent(
            client=client,
            definition=reviewer_agent_definition,
        )

        # 3. Create the copy writer agent on the Azure AI agent service
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
        )

        # 4. Create a Semantic Kernel agent for the copy writer Azure AI agent
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
        )

        # 5. Place the agents in a group chat with a custom termination strategy
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        try:
            # 6. Add the task as a message to the group chat
            await chat.add_chat_message(message=TASK)
            print(f"# {AuthorRole.USER}: '{TASK}'")
            # 7. Invoke the chat
            async for content in chat.invoke():
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
        finally:
            # 8. Cleanup: Delete the agents
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)

        """
        Sample Output:
        # AuthorRole.USER: 'a slogan for a new line of electric cars.'
        # AuthorRole.ASSISTANT - CopyWriter: '"Charge Ahead: Drive the Future."'
        # AuthorRole.ASSISTANT - ArtDirector: 'This slogan has a nice ring to it and captures the ...'
        # AuthorRole.ASSISTANT - CopyWriter: '"Plug In. Drive Green."'
        ...
        """


if __name__ == "__main__":
    asyncio.run(main())
