# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentGroupChat, AzureAssistantAgent, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureOpenAISettings
from semantic_kernel.contents import AuthorRole
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat to work towards
the user's requirement.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    # First create a ChatCompletionAgent
    agent_reviewer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("artdirector"),
        name="ArtDirector",
        instructions="""
            You are an art director who has opinions about copywriting born of a love for David Ogilvy.
            The goal is to determine if the given copy is acceptable to print.
            If so, state that it is approved. Only include the word "approved" if it is so.
            If not, provide insight on how to refine suggested copy without example.
            """,
    )

    # Next, we will create the AzureAssistantAgent

    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        name="CopyWriter",
        instructions="""
        You are a copywriter with ten years of experience and are known for brevity and a dry humor.
        The goal is to refine and decide on the single best copy as an expert in the field.
        Only provide a single proposal per response.
        You're laser focused on the goal at hand.
        Don't waste time with chit chat.
        Consider suggestions when refining an idea.
        """,
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent_writer = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Create the AgentGroupChat object, which will manage the chat between the agents
    chat = AgentGroupChat(
        agents=[agent_writer, agent_reviewer],
        termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
    )

    input = "a slogan for a new line of electric cars."

    try:
        await chat.add_chat_message(input)
        print(f"# {AuthorRole.USER}: '{input}'")

        last_agent = None
        async for message in chat.invoke_stream():
            if message.content is not None:
                if last_agent != message.name:
                    print(f"\n# {message.name}: ", end="", flush=True)
                    last_agent = message.name
                print(f"{message.content}", end="", flush=True)

        print()
        print(f"# IS COMPLETE: {chat.is_complete}")
    finally:
        await agent_writer.client.beta.assistants.delete(agent_writer.id)


if __name__ == "__main__":
    asyncio.run(main())
