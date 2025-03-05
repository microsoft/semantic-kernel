# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai import AzureAssistantAgent, OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and retrieve the    #
# assistant using the `retrieve` class method.                      #
#####################################################################

AGENT_NAME = "JokeTeller"
AGENT_INSTRUCTIONS = "You are a funny comedian who loves telling G-rated jokes."

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = True


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=input))

    print(f"# {AuthorRole.USER}: '{input}'")

    async for message in agent.invoke(thread_id=thread_id):
        if message.content:
            print(f"# {message.role}: {message.content}")

        if len(message.items) > 0:
            for item in message.items:
                if isinstance(item, FileReferenceContent):
                    print(f"\n`{message.role}` => {item.file_id}")


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Define a service_id for the sample
    service_id = "agent"

    # Specify an assistant ID which is used
    # to retrieve the agent
    assistant_id: str = None

    # Create the agent configuration
    if use_azure_openai:
        agent = await AzureAssistantAgent.create(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_code_interpreter=True,
        )

        assistant_id = agent.assistant.id

        retrieved_agent: AzureAssistantAgent = await AzureAssistantAgent.retrieve(
            id=assistant_id,
            kernel=kernel,
        )
    else:
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_code_interpreter=True,
        )

        assistant_id = agent.assistant.id

        # Retrieve the agent using the assistant_id
        retrieved_agent: OpenAIAssistantAgent = await OpenAIAssistantAgent.retrieve(
            id=assistant_id,
            kernel=kernel,
        )

    # Define a thread and invoke the agent with the user input
    thread_id = await retrieved_agent.create_thread()

    try:
        await invoke_agent(retrieved_agent, thread_id, "Tell me a joke about bears.")
    finally:
        await agent.delete()
        await retrieved_agent.delete_thread(thread_id)


if __name__ == "__main__":
    asyncio.run(main())
