# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI, a chat completion  #
# agent and have them participate in a group chat to work towards   #
# the user's requirement.                                           #
#####################################################################


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


async def main():
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        # Create the reviewer agent definition
        reviewer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )
        # Create the reviewer Azure AI Agent
        agent_reviewer = AzureAIAgent(
            client=client,
            definition=reviewer_agent_definition,
        )

        # Create the copy writer agent definition
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
        )
        # Create the copy writer Azure AI Agent
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
        )

        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        input = "a slogan for a new line of electric cars."

        try:
            await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
            print(f"# {AuthorRole.USER}: '{input}'")

            async for content in chat.invoke():
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

            print(f"# IS COMPLETE: {chat.is_complete}")

            print("*" * 60)
            print("Chat History (In Descending Order):\n")
            async for message in chat.get_chat_messages(agent=agent_reviewer):
                print(f"# {message.role} - {message.name or '*'}: '{message.content}'")
        finally:
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)


if __name__ == "__main__":
    asyncio.run(main())
